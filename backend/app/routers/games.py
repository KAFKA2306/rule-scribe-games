from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.rate_limiter import RateLimiter
from app.models import GameDetail, GameListResponse, GameUpdate, SearchRequest
from app.models.rule_graph import RuleGraphReadResponse, RuleNodeType
from app.routers.auth import require_catalog_editor
from app.services import catalog_access
from app.services.game_service import GameService
from app.services.rule_graph import RuleGraphService

router = APIRouter()

# Shared limiters
search_limiter = RateLimiter.get_limiter("search", max_requests=100, window_seconds=60)
gen_limiter = RateLimiter.get_limiter("generation", max_requests=10, window_seconds=60)


def get_game_service():
    return GameService()


def get_rule_graph_service():
    return RuleGraphService()


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
    # Always honor the DB-first contract even when a legacy client asks to generate.
    matches = await service.search_games(body.query.strip())
    if matches:
        return matches

    if body.generate:
        if not gen_limiter.acquire():
            raise HTTPException(status_code=429, detail="Generation rate limit exceeded")

        new_game = await service.create_game_from_query(body.query.strip())
        if new_game and new_game.get("slug"):
            return [new_game]
    return []


@router.get("/games", response_model=GameListResponse)
async def list_recent_games(limit: int = 100, offset: int = 0, service: GameService = Depends(get_game_service)):
    result = await service.list_recent_games(limit=limit, offset=offset)
    return {
        "games": result["data"],
        "total": result["total"] or 0,
        "limit": limit,
        "offset": offset,
    }


@router.get("/games/{slug}/rule-graph", response_model=RuleGraphReadResponse)
async def get_game_rule_graph(
    slug: str,
    types: list[RuleNodeType] | None = Query(default=None),
    service: RuleGraphService = Depends(get_rule_graph_service),
):
    graph = await service.get_by_slug(slug, rule_types=types)
    if graph is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return graph


@router.get("/games/{slug}", response_model=GameDetail)
async def get_game_details(slug: str, service: GameService = Depends(get_game_service)):
    game = await service.get_game_by_slug(slug)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game


@router.patch("/games/{slug}")
async def update_game(
    slug: str,
    game_update: GameUpdate | None = None,
    regenerate: bool = False,
    fill_missing_only: bool = False,
    editor: dict = Depends(require_catalog_editor),
    service: GameService = Depends(get_game_service),
) -> dict[str, object]:
    try:
        if regenerate:
            if not gen_limiter.acquire():
                raise HTTPException(status_code=429, detail="Generation rate limit exceeded")
            result = await service.update_game_content(slug, fill_missing_only=fill_missing_only)
            await catalog_access.record_catalog_mutation(
                editor_user_id=str(editor["id"]),
                game=result,
                slug=slug,
                action="regenerate",
                changed_fields=[
                    "rules_content",
                    "structured_data",
                    "min_players",
                    "max_players",
                    "play_time",
                    "min_age",
                    "bga_url",
                    "content_review_status",
                    "data_version",
                ],
            )
            return result

        if game_update:
            updates = game_update.model_dump(exclude_unset=True)
            if updates:
                result = await service.update_game_manual(slug, updates)
                await catalog_access.record_catalog_mutation(
                    editor_user_id=str(editor["id"]),
                    game=result,
                    slug=slug,
                    action="manual_update",
                    changed_fields=list(updates),
                )
                return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found") from exc

    return {"status": "ok", "message": "No action taken (regenerate=False, no body)"}
