import re
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from app.core.supabase import supabase_repository
from app.services.gemini_client import GeminiClient

router = APIRouter()
gemini = GeminiClient()


class SearchResult(BaseModel):
    id: int | str
    slug: Optional[str] = None
    title: str
    description: Optional[str] = None
    rules_content: Optional[str] = None
    image_url: Optional[str] = None
    summary: Optional[str] = None
    structured_data: Optional[dict] = None
    source_url: Optional[str] = None


class SearchRequest(BaseModel):
    query: str


@router.post("/search", response_model=List[SearchResult])
async def search(req: SearchRequest):
    clean_query = req.query.strip()

    # Check if this is an update request for an existing game
    # We'll let Gemini decide if it's an update, but we can try to find context if possible
    # For now, we just pass the query to Gemini and let it handle the logic
    # If Gemini returns a game that matches an existing one (by title/url), upsert will update it.

    if not clean_query.startswith("http"):
        # Only try DB search if it looks like a simple title search, not a complex update command
        # Simple heuristic: if it's short and doesn't contain "update"/"add"/"change"
        is_simple_search = len(clean_query) < 50 and not any(
            k in clean_query.lower()
            for k in ["update", "add", "change", "更新", "追加"]
        )

        if is_simple_search:
            if res := await supabase_repository.search(clean_query):
                return [SearchResult(**r) for r in res]

    data = await gemini.extract_game_info(clean_query)

    if "error" in data:
        from fastapi import HTTPException

        error_msg = data["error"]
        raise HTTPException(
            status_code=500, detail=f"AI生成に失敗しました: {error_msg}"
        )

    data["source_url"] = (
        clean_query if clean_query.startswith("http") else _derived_source(data)
    )

    if saved := await supabase_repository.upsert(data):
        return [SearchResult(**r) for r in saved]

    return [SearchResult(**{**data, "id": 0})]


def _derived_source(data: dict) -> str:
    """
    Create a deterministic pseudo-source for non-URL queries so that upsert
    can deduplicate logically identical games without a DB schema change.
    """
    title = data.get("title") or ""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "unknown"
    return f"derived://title/{slug}"


@router.get("/games", response_model=List[SearchResult])
async def list_games(limit: int = 100):
    """
    Simple listing endpoint so the frontend can show Supabase data
    immediately without requiring a search query.
    """
    safe_limit = min(max(limit, 1), 200)
    if res := await supabase_repository.list_recent(safe_limit):
        return [SearchResult(**r) for r in res]
    return []
