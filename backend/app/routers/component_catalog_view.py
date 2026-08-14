from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.component_catalog import ComponentKind
from app.models.component_catalog_view import (
    ComponentCatalogAvailabilityResponse,
    ComponentCatalogPageResponse,
)
from app.services.component_catalog_view import ComponentCatalogViewService

router = APIRouter()


def get_component_catalog_view_service():
    return ComponentCatalogViewService()


@router.get(
    "/games/{slug}/component-catalog-availability",
    response_model=ComponentCatalogAvailabilityResponse,
)
async def get_component_catalog_availability(
    slug: str,
    service: ComponentCatalogViewService = Depends(get_component_catalog_view_service),
):
    result = await service.get_availability(slug)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return result


@router.get(
    "/games/{slug}/component-catalog",
    response_model=ComponentCatalogPageResponse,
)
async def get_component_catalog_page(
    slug: str,
    rule_set_id: str = Query(..., min_length=1),
    component_set_id: str | None = Query(default=None),
    kind: ComponentKind | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ComponentCatalogViewService = Depends(get_component_catalog_view_service),
):
    result = await service.get_page(
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
