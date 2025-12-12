from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.models import GameDetail, GameUpdate
from app.services.game_service import GameService

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    generate: bool = False


def get_game_service():
    return GameService()


@router.get("/search", response_model=List[GameDetail])
async def search_games(
    q: str = Query(..., min_length=1), service: GameService = Depends(get_game_service)
):
    return await service.search_games(q)


@router.post("/search", response_model=List[GameDetail])
async def search_games_post(
    body: SearchRequest,
    service: GameService = Depends(get_game_service),
):
    if body.generate:
        new_game = await service.create_game_from_query(body.query)
        if new_game and new_game.get("slug"):
            return [new_game]

    return await service.search_games(body.query)


@router.get("/games", response_model=List[GameDetail])
async def list_recent_games(
    limit: int = 100, offset: int = 0, service: GameService = Depends(get_game_service)
):
    return await service.list_recent_games(limit=limit, offset=offset)


@router.get("/games/{slug}", response_model=GameDetail)
async def get_game_details(slug: str, service: GameService = Depends(get_game_service)):
    game = await service.get_game_by_slug(slug)

    return game


@router.patch("/games/{slug}")
async def update_game(
    slug: str,
    game_update: Optional[GameUpdate] = None,
    regenerate: bool = False,
    fill_missing_only: bool = False,
    service: GameService = Depends(get_game_service),
):
    if regenerate:
        return await service.update_game_content(
            slug, fill_missing_only=fill_missing_only
        )

    if game_update:
        updates = game_update.model_dump(exclude_unset=True)
        if updates:
            return await service.update_game_manual(slug, updates)

    return {"status": "ok", "message": "No action taken (regenerate=False, no body)"}
