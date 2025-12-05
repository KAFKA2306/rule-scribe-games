from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from typing import List
from pydantic import BaseModel
from api.app.models import GameDetail
from api.app.services.game_service import GameService

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
    background_tasks: BackgroundTasks,
    service: GameService = Depends(get_game_service),
):
    if body.generate:
        new_game = await service.create_game_from_query(body.query, background_tasks)
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
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.patch("/games/{slug}")
async def update_game(
    slug: str,
    background_tasks: BackgroundTasks,
    regenerate: bool = False,
    service: GameService = Depends(get_game_service),
):
    if regenerate:
        return await service.update_game_content(slug, background_tasks)

    return {"status": "ok", "message": "No action taken (regenerate=False)"}
