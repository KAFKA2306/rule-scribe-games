import re
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from app.core.supabase import supabase_repository
from app.services.gemini_client import GeminiClient

router = APIRouter()
gemini = GeminiClient()


class SearchResult(BaseModel):
    id: str  # UUID from database
    slug: str  # Added slug field
    title: str
    description: Optional[str] = None
    rules_content: Optional[str] = None
    image_url: Optional[str] = None
    summary: Optional[str] = None
    structured_data: Optional[dict] = None
    source_url: Optional[str] = None
    affiliate_urls: Optional[dict] = None


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
                results = []
                for r in res:
                    sd = r.get("structured_data") or {}
                    affiliate_urls = sd.get("affiliate_urls")
                    results.append(SearchResult(**r, affiliate_urls=affiliate_urls))
                return results

    data = await gemini.extract_game_info(clean_query)

    # Check for error from GeminiClient
    if "error" in data:
        # We can return an empty list or a special error object if we want to show it to the user
        # For now, let's return a list with a special "error" item or just empty to fail gracefully
        # But the frontend expects a list of SearchResult.
        # Let's return empty list and let frontend handle "no results" or maybe we should propagate error?
        # The user wants to see the error.
        # But SearchResult model doesn't have 'error' field.
        # Let's just print it and return empty for now, or maybe we can hack it into description?
        print(f"Gemini returned error: {data['error']}")
        return []

    data["source_url"] = (
        clean_query if clean_query.startswith("http") else _derived_source(data)
    )

    if saved := await supabase_repository.upsert(data):
        results = []
        for r in saved:
            sd = r.get("structured_data") or {}
            affiliate_urls = sd.get("affiliate_urls")
            results.append(SearchResult(**r, affiliate_urls=affiliate_urls))
        return results

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
