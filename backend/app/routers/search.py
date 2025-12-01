from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.core.supabase import search_games

router = APIRouter()

class SearchRequest(BaseModel):
    query: str

class SearchResult(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    rules_content: Optional[str] = None

@router.post("/search", response_model=List[SearchResult])
async def search(request: SearchRequest):
    results = search_games(request.query)
    return results
