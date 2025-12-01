from fastapi import APIRouter
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
    data = request.model_dump()
    data["id"] = game_id
    res = supabase_manager.client.table("games").update(data).eq("id", game_id).execute()
    return SearchResult(**res.data[0])

@router.post("/search", response_model=List[SearchResult])
async def search(req: SearchRequest):
    if not req.query.startswith("http"):
        if res := search_games(req.query): return [SearchResult(**r) for r in res]

    data = gemini.extract_game_info(req.query)
    data["source_url"] = req.query if req.query.startswith("http") else None
    if saved := supabase_manager.upsert_game(data):
        return [SearchResult(**r) for r in saved]
    return [SearchResult(**{**data, "id": 0})]
