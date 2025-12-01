from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.core.supabase import search_games, supabase_manager
from app.services.gemini_client import GeminiClient

router = APIRouter()
gemini = GeminiClient()

class SearchResult(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    rules_content: Optional[str] = None
    image_url: Optional[str] = None

class UpdateGameRequest(BaseModel):
    title: str
    description: Optional[str]
    rules_content: Optional[str]
    image_url: Optional[str]

class SearchRequest(BaseModel):
    query: str

@router.put("/games/{game_id}", response_model=SearchResult)
async def update_game(game_id: int, request: UpdateGameRequest):
    if not supabase_manager.is_connected: raise HTTPException(503, "DB disconnected")
    try:
        data = request.model_dump()
        data["id"] = game_id
        res = supabase_manager.client.table("games").update(data).eq("id", game_id).execute()
        if not res.data: raise HTTPException(404, "Game not found")
        return SearchResult(**res.data[0])
    except Exception as e: raise HTTPException(500, str(e))

@router.post("/search", response_model=List[SearchResult])
async def search(req: SearchRequest):
    # Try DB first unless URL
    if not req.query.startswith("http"):
        if res := search_games(req.query): return [SearchResult(**r) for r in res]

    # Fallback to Web Extraction
    try:
        data = gemini.extract_game_info(req.query)
        if data.get("title") != "Unknown":
            if "error" in data: del data["error"]
            data["source_url"] = req.query if req.query.startswith("http") else None
            if saved := supabase_manager.upsert_game(data):
                return [SearchResult(**r) for r in saved]
            return [SearchResult(**{**data, "id": 0})]
    except Exception as e: print(f"Web search failed: {e}")
    
    return []
