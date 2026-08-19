from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError

from app.core.rate_limiter import RateLimiter
from app.models import GameDetail, GameListResponse, GameUpdate, SearchRequest
from app.models.component_catalog import (
    ComponentDetailResponse,
    ComponentKind,
    ComponentListResponse,
    ComponentSetListResponse,
)
from app.models.concept_taxonomy import ConceptDetailResponse, GameConceptsReadResponse, GameGlossaryReadResponse
from app.models.evidence import (
    ClaimDetailResponse,
    ClaimTarget,
    EvidenceTargetType,
    EvidenceTraceResponse,
)
from app.models.rule_graph import RuleGraphReadResponse, RuleNodeType
from app.models.ruleset import RuleSetListResponse
from app.routers.auth import require_catalog_editor
from app.services import catalog_access
from app.services.component_catalog import ComponentCatalogService
from app.services.concept_taxonomy import ConceptTaxonomyService
from app.services.evidence import EvidenceService
from app.services.game_service import GameService, UnverifiedGameIdentityError
from app.services.rule_graph import RuleGraphService
from app.services.rulesets import RuleSetService

router = APIRouter()

# Shared limiters
search_limiter = RateLimiter.get_limiter("search", max_requests=100, window_seconds=60)
gen_limiter = RateLimiter.get_limiter("generation", max_requests=10, window_seconds=60)


def get_game_service():
    return GameService()


def get_rule_graph_service():
    return RuleGraphService()


def get_ruleset_service():
    return RuleSetService()


def get_component_catalog_service():
    return ComponentCatalogService()


def get_evidence_service():
    return EvidenceService()


def get_concept_taxonomy_service():
    return ConceptTaxonomyService()


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
    # Legacy clients may still send generate=true. Public search is deliberately
    # read-only; catalog generation requires an authenticated editor workflow.
    if body.generate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Catalog generation is not available from public search",
        )
    if not search_limiter.acquire():
        raise HTTPException(status_code=429, detail="Search rate limit exceeded")
    if not body.query or not body.query.strip():
        return []
    return await service.search_games(body.query.strip())


@router.get("/games", response_model=GameListResponse)
async def list_recent_games(limit: int = 100, offset: int = 0, service: GameService = Depends(get_game_service)):
    result = await service.list_recent_games(limit=limit, offset=offset)
    return {
        "games": result["data"],
        "total": result["total"] or 0,
        "limit": limit,
        "offset": offset,
    }


@router.get("/concepts/{concept_id}", response_model=ConceptDetailResponse)
async def get_concept_detail(
    concept_id: str,
    service: ConceptTaxonomyService = Depends(get_concept_taxonomy_service),
):
    concept = await service.get_concept(concept_id)
    if concept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")
    return concept


@router.get("/games/{slug}/concepts", response_model=GameConceptsReadResponse)
async def get_game_concepts(
    slug: str,
    service: ConceptTaxonomyService = Depends(get_concept_taxonomy_service),
):
    concepts = await service.get_by_game_slug(slug)
    if concepts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return concepts


@router.get("/games/{slug}/glossary", response_model=GameGlossaryReadResponse)
async def get_game_glossary(
    slug: str,
    language_code: str = Query(default="ja", min_length=2, max_length=35),
    service: ConceptTaxonomyService = Depends(get_concept_taxonomy_service),
):
    glossary = await service.get_glossary_by_game_slug(slug, language_code=language_code)
    if glossary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return glossary


@router.get("/games/{slug}/rule-sets", response_model=RuleSetListResponse)
async def get_game_rule_sets(
    slug: str,
    service: RuleSetService = Depends(get_ruleset_service),
):
    rulesets = await service.get_by_slug(slug)
    if rulesets is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return rulesets


@router.get("/games/{slug}/component-sets", response_model=ComponentSetListResponse)
async def get_game_component_sets(
    slug: str,
    rule_set_id: str = Query(..., min_length=1),
    service: ComponentCatalogService = Depends(get_component_catalog_service),
):
    result = await service.get_sets(slug, rule_set_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return result


@router.get("/games/{slug}/components", response_model=ComponentListResponse)
async def list_game_components(
    slug: str,
    rule_set_id: str = Query(..., min_length=1),
    component_set_id: str | None = Query(default=None),
    kind: ComponentKind | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: ComponentCatalogService = Depends(get_component_catalog_service),
):
    result = await service.list_components(
        slug,
        rule_set_id,
        component_set_id=component_set_id,
        kind=kind.value if kind else None,
        limit=limit,
        offset=offset,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return result


@router.get("/games/{slug}/components/{component_id}", response_model=ComponentDetailResponse)
async def get_game_component(
    slug: str,
    component_id: str,
    rule_set_id: str = Query(..., min_length=1),
    service: ComponentCatalogService = Depends(get_component_catalog_service),
):
    result = await service.get_component(slug, rule_set_id, component_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
    return result


@router.get("/games/{slug}/evidence", response_model=EvidenceTraceResponse)
async def get_game_evidence_trace(
    slug: str,
    rule_set_id: str = Query(..., min_length=1),
    target_type: EvidenceTargetType = Query(...),
    rule_id: str | None = Query(default=None),
    component_id: str | None = Query(default=None),
    component_set_id: str | None = Query(default=None),
    property_key: str | None = Query(default=None),
    ordinal: int | None = Query(default=None, ge=0),
    ability_id: str | None = Query(default=None),
    field_path: str | None = Query(default=None),
    service: EvidenceService = Depends(get_evidence_service),
):
    try:
        target = ClaimTarget(
            target_type=target_type,
            rule_id=rule_id,
            component_id=component_id,
            component_set_id=component_set_id,
            property_key=property_key,
            ordinal=ordinal,
            ability_id=ability_id,
            field_path=field_path,
        )
    except ValidationError as exc:
        detail = exc.errors(include_context=False, include_input=False, include_url=False)
        raise HTTPException(status_code=422, detail=detail) from exc
    result = await service.get_trace(slug, rule_set_id, target)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return result


@router.get("/games/{slug}/claims/{claim_id}", response_model=ClaimDetailResponse)
async def get_game_claim_detail(
    slug: str,
    claim_id: str,
    rule_set_id: str = Query(..., min_length=1),
    service: EvidenceService = Depends(get_evidence_service),
):
    result = await service.get_claim(slug, rule_set_id, claim_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return result


@router.get("/games/{slug}/rule-graph", response_model=RuleGraphReadResponse)
async def get_game_rule_graph(
    slug: str,
    types: list[RuleNodeType] | None = Query(default=None),
    rule_set_id: str | None = Query(default=None),
    service: RuleGraphService = Depends(get_rule_graph_service),
):
    graph = await service.get_by_slug(slug, rule_types=types, rule_set_id=rule_set_id)
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
    except UnverifiedGameIdentityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found") from exc

    return {"status": "ok", "message": "No action taken (regenerate=False, no body)"}
