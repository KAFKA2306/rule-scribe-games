import re
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from app.core.supabase import supabase_repository
from app.services.gemini_client import GeminiClient

router = APIRouter()
gemini = GeminiClient()


class SearchResult(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    rules_content: Optional[str] = None
    image_url: Optional[str] = None
    summary: Optional[str] = None


class SearchRequest(BaseModel):
    query: str


@router.post("/search", response_model=List[SearchResult])
async def search(req: SearchRequest):
    clean_query = req.query.strip()
    if not clean_query.startswith("http"):
        try:
            if res := await supabase_repository.search(clean_query):
                return [SearchResult(**r) for r in res]
        except Exception:
            # If DB search fails, continue to AI search
            pass

    try:
        data = await gemini.extract_game_info(clean_query)
    except Exception:
        # If AI search completely blows up despite safeguards
        return []

    data["source_url"] = (
        clean_query if clean_query.startswith("http") else _derived_source(data)
    )
    
    try:
        if saved := await supabase_repository.upsert(data):
            return [SearchResult(**r) for r in saved]
    except Exception:
        # If upsert fails, just return what we have
        pass
    
    # Return result with provisional ID 0
    return [SearchResult(**{**data, "id": 0})]


def _derived_source(data: dict) -> str:
    """
    Create a deterministic pseudo-source for non-URL queries so that upsert
    can deduplicate logically identical games without a DB schema change.
    """
    title = data.get("title") or ""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "unknown"
    return f"derived://title/{slug}"
