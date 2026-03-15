from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.rate_limiter import RateLimiter
from app.models import GameDetail, GameUpdate, SearchRequest
from app.services.game_service import GameService

router = APIRouter()

# Shared limiters
search_limiter = RateLimiter.get_limiter("search", max_requests=100, window_seconds=60)
gen_limiter = RateLimiter.get_limiter("generation", max_requests=10, window_seconds=60)


def get_game_service():
    return GameService()


@router.get("/search", response_model=list[GameDetail])
async def search_games(q: str = Query(..., min_length=1), service: GameService = Depends(get_game_service)):
    if not search_limiter.acquire():
        raise HTTPException(status_code=429, detail="Search rate limit exceeded")

    if not q or not q.strip():
        return []
    return await service.search_games(q.strip())


@router.post("/search", response_model=list[GameDetail])
async def search_games_post(
    body: SearchRequest,
    service: GameService = Depends(get_game_service),
):
    if body.generate:
        if not gen_limiter.acquire():
            raise HTTPException(status_code=429, detail="Generation rate limit exceeded")

        new_game = await service.generate_with_notebooklm(body.query)
        if new_game and new_game.get("slug"):
            return [new_game]
    return await service.search_games(body.query)


@router.get("/games", response_model=list[GameDetail])
async def list_recent_games(limit: int = 100, offset: int = 0, service: GameService = Depends(get_game_service)):
    return await service.list_recent_games(limit=limit, offset=offset)


@router.get("/games/{slug}", response_model=GameDetail)
async def get_game_details(slug: str, service: GameService = Depends(get_game_service)):
    game = await service.get_game_by_slug(slug)
    return game


@router.patch("/games/{slug}")
async def update_game(
    slug: str,
    game_update: GameUpdate | None = None,
    regenerate: bool = False,
    fill_missing_only: bool = False,
    service: GameService = Depends(get_game_service),
) -> dict[str, object]:
    if regenerate:
        if not gen_limiter.acquire():
            raise HTTPException(status_code=429, detail="Generation rate limit exceeded")
        return await service.update_game_content(slug, fill_missing_only=fill_missing_only)

    if game_update:
        updates = game_update.model_dump(exclude_unset=True)
        if updates:
            return await service.update_game_manual(slug, updates)

    return {"status": "ok", "message": "No action taken (regenerate=False, no body)"}
