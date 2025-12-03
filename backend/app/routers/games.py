from fastapi import APIRouter, HTTPException
# Force reload
from typing import List, Optional
from pydantic import BaseModel
from app.core.supabase import supabase_repository

from app.services.amazon_affiliate import amazon_search_url

router = APIRouter(prefix="/games", tags=["games"])


class GameDetail(BaseModel):
    id: str
    slug: str
    title: str
    description: Optional[str] = None
    rules_content: Optional[str] = None
    image_url: Optional[str] = None
    summary: Optional[str] = None
    structured_data: Optional[dict] = None
    source_url: Optional[str] = None
    affiliate_urls: Optional[dict] = None
    view_count: Optional[int] = 0
    search_count: Optional[int] = 0
    data_version: Optional[int] = 0
    is_official: Optional[bool] = False
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    play_time: Optional[int] = None
    min_age: Optional[int] = None
    published_year: Optional[int] = None
    title_ja: Optional[str] = None
    title_en: Optional[str] = None
    official_url: Optional[str] = None
    bgg_url: Optional[str] = None
    bga_url: Optional[str] = None
    amazon_url: Optional[str] = None
    audio_url: Optional[str] = None


@router.get("", response_model=List[GameDetail])
async def list_games():
    games = await supabase_repository.list_recent(limit=100)
    results = []
    for g in games:
        sd = g.get("structured_data") or {}
        affiliate_urls = sd.get("affiliate_urls") or {}
        
        # Inject Amazon link if missing
        if "amazon" not in affiliate_urls:
            if url := amazon_search_url(g["title"]):
                affiliate_urls["amazon"] = url
                
        results.append(GameDetail(**g, affiliate_urls=affiliate_urls or None))
    return results


@router.get("/{slug}", response_model=GameDetail)
async def get_game_by_slug(slug: str):
    game = await supabase_repository.get_by_slug(slug)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    sd = game.get("structured_data") or {}
    affiliate_urls = sd.get("affiliate_urls") or {}
    
    # Inject Amazon link if missing
    if "amazon" not in affiliate_urls:
        if url := amazon_search_url(game["title"]):
            affiliate_urls["amazon"] = url

    return GameDetail(**game, affiliate_urls=affiliate_urls or None)
