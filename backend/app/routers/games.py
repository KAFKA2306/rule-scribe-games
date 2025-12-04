from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from app.core.supabase import supabase_repository
from app.services.amazon_affiliate import amazon_search_url
from app.services.data_enhancer import DataEnhancer
from app.models import GameDetail
from app.services.gemini_client import GeminiClient

router = APIRouter(prefix="/games", tags=["games"])


@router.get("", response_model=List[GameDetail])
async def list_games(limit: int = 50, offset: int = 0):
    games = await supabase_repository.list_recent(limit=min(limit, 100), offset=offset)
    results = []
    for g in games:
        sd = g.get("structured_data") or {}
        affiliate_urls = sd.get("affiliate_urls") or {}

        if "amazon" not in affiliate_urls:
            if url := amazon_search_url(g["title"]):
                affiliate_urls["amazon"] = url

        results.append(GameDetail(**g, affiliate_urls=affiliate_urls or None))
    return results


@router.get("/{slug}", response_model=GameDetail)
async def get_game_by_slug(slug: str, background_tasks: BackgroundTasks):
    game = await supabase_repository.get_by_slug(slug)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Background Data Enhancement
    enhancer = DataEnhancer()
    if await enhancer.should_enhance(game):
        background_tasks.add_task(run_background_enhancement, game)

    sd = game.get("structured_data") or {}
    affiliate_urls = sd.get("affiliate_urls") or {}

    if "amazon" not in affiliate_urls:
        if url := amazon_search_url(game["title"]):
            affiliate_urls["amazon"] = url

    return GameDetail(**game, affiliate_urls=affiliate_urls or None)


async def run_background_enhancement(game: dict):
    try:
        enhancer = DataEnhancer()
        enhanced_game = await enhancer.enhance(game)
        
        # If data changed (version increased), save it
        if enhanced_game.get("data_version", 0) > game.get("data_version", 0):
            await supabase_repository.upsert(enhanced_game)
            print(f"Background enhancement saved for {game.get('title')}")
    except Exception as e:
        print(f"Background enhancement failed for {game.get('title')}: {e}")


class UpdateGameRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    rules_content: Optional[str] = None
    image_url: Optional[str] = None
    summary: Optional[str] = None
    structured_data: Optional[dict] = None
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    play_time: Optional[int] = None
    min_age: Optional[int] = None
    published_year: Optional[int] = None
    title_ja: Optional[str] = None
    title_en: Optional[str] = None
    official_url: Optional[str] = None
    bgg_url: Optional[str] = None
    regenerate: Optional[bool] = False




@router.patch("/{slug}", response_model=GameDetail)
async def update_game(slug: str, update_data: UpdateGameRequest):
    existing_game = await supabase_repository.get_by_slug(slug)
    if not existing_game:
        raise HTTPException(status_code=404, detail="Game not found")

    data_to_update = {k: v for k, v in update_data.dict().items() if v is not None and k != "regenerate"}

    if update_data.regenerate:
        print(f"Regenerating game data for: {existing_game.get('title')}")
        gemini_client = GeminiClient()
        # Use existing title for regeneration
        query = existing_game.get("title") or existing_game.get("title_ja") or existing_game.get("title_en")
        if not query:
             raise HTTPException(status_code=400, detail="Cannot regenerate: No title found")
             
        generated_data = await gemini_client.extract_game_info(query)
        
        if "error" in generated_data:
            raise HTTPException(status_code=500, detail=generated_data["error"])

        allowed_fields = {
            "title", "title_ja", "title_en", "description", "rules_content",
            "image_url", "min_players", "max_players", "play_time",
            "min_age", "published_year", "official_url", "bgg_url",
            "structured_data", "summary"
        }
        
        filtered_generated = {k: v for k, v in generated_data.items() if k in allowed_fields}
        data_to_update.update(filtered_generated)

    if not data_to_update:
        raise HTTPException(status_code=400, detail="No fields to update")

    merged_data = {**existing_game, **data_to_update}

    if "id" not in merged_data:
        merged_data["id"] = existing_game["id"]

    try:
        updated_games = await supabase_repository.upsert(merged_data)
        if not updated_games:
            raise HTTPException(status_code=500, detail="Failed to update game")

        game = updated_games[0]
        sd = game.get("structured_data") or {}
        affiliate_urls = sd.get("affiliate_urls") or {}
        return GameDetail(**game, affiliate_urls=affiliate_urls or None)

    except Exception as e:
        print(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
