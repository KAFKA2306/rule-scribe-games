from fastapi import APIRouter, HTTPException
from app.core.supabase import supabase_repository

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/{slug}")
async def get_game_by_slug(slug: str):
    game = await supabase_repository.get_by_slug(slug)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
