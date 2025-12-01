import re
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from app.core.supabase import supabase_repository
from app.services.gemini_client import GeminiClient

router = APIRouter()
gemini = GeminiClient()
logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    rules_content: Optional[str] = None
    image_url: Optional[str] = None


class SearchRequest(BaseModel):
    query: str


@router.post("/search", response_model=List[SearchResult])
async def search(req: SearchRequest):
    """
    Search for a game.
    1. Check Supabase cache (if available).
    2. If not found, ask Gemini to find/scrape it.
    3. Save result to Supabase.
    Returns a list of results (usually 1 if from Gemini, multiple if from DB).
    Gracefully degrades to empty list or error-info on failure.
    """
    try:
        clean_query = req.query.strip()
        if not clean_query:
            return []

        # 1. Try DB Search
        # Note: supabase_repository is already guarded to return [] on failure
        if not clean_query.startswith("http"):
            try:
                if res := await supabase_repository.search(clean_query):
                    return [SearchResult(**r) for r in res]
            except Exception as e:
                logger.warning(f"DB search failed (ignoring): {e}")

        # 2. Ask Gemini
        # gemini.extract_game_info is guarded to return a dict (mock or real) or error dict
        data = await gemini.extract_game_info(clean_query)

        data["source_url"] = (
            clean_query if clean_query.startswith("http") else _derived_source(data)
        )

        # 3. Save to DB
        # supabase_repository.upsert is guarded
        try:
            if saved := await supabase_repository.upsert(data):
                return [SearchResult(**r) for r in saved]
        except Exception as e:
            logger.warning(f"DB upsert failed (ignoring): {e}")

        # Return what we got from Gemini (mock or real) with a fake ID
        return [SearchResult(**{**data, "id": 0})]

    except Exception as e:
        logger.error(f"Unhandled search error: {e}")
        # Return a safe fallback to satisfy response_model
        return [
            SearchResult(
                id=-1,
                title="System Error",
                description="An error occurred while processing your request.",
                rules_content=str(e)
            )
        ]


def _derived_source(data: dict) -> str:
    """
    Create a deterministic pseudo-source for non-URL queries so that upsert
    can deduplicate logically identical games without a DB schema change.
    """
    title = data.get("title") or ""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "unknown"
    return f"derived://title/{slug}"
