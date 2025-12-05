from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from typing import List
from app.models import GameDetail
from app.services.game_service import GameService

router = APIRouter()

def get_game_service():
    return GameService()

@router.get("/search", response_model=List[GameDetail])
async def search_games(
    q: str = Query(..., min_length=1),
    service: GameService = Depends(get_game_service)
):
    """Search for games by title or description."""
    return await service.search_games(q)


@router.get("/games", response_model=List[GameDetail])
async def list_recent_games(
    limit: int = 100, 
    offset: int = 0,
    service: GameService = Depends(get_game_service)
):
    """List recently updated games."""
    return await service.list_recent_games(limit=limit, offset=offset)


@router.get("/games/{slug}", response_model=GameDetail)
async def get_game_details(
    slug: str,
    service: GameService = Depends(get_game_service)
):
    """Get detailed information about a specific game by slug."""
    game = await service.get_game_by_slug(slug)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.patch("/games/{slug}")
async def update_game(
    slug: str, 
    background_tasks: BackgroundTasks, 
    regenerate: bool = False,
    service: GameService = Depends(get_game_service)
):
    """
    Trigger an update for a game.
    If regenerate=True, it runs the research agent to fetch fresh data.
    """
    if regenerate:
        return await service.regenerate_game(slug, background_tasks)

    return {"status": "ok", "message": "No action taken (regenerate=False)"}
