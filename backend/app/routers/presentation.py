from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.presentation_projection import PresentationProjectionResponse
from app.services.presentation_projection import PresentationProjectionService

router = APIRouter()


def get_presentation_projection_service():
    return PresentationProjectionService()


@router.get(
    "/games/{slug}/presentation",
    response_model=PresentationProjectionResponse,
)
async def get_game_presentation_projection(
    slug: str,
    rule_set_id: str = Query(..., min_length=1),
    language_code: str = Query(default="ja", min_length=2, max_length=35),
    service: PresentationProjectionService = Depends(get_presentation_projection_service),
):
    projection = await service.get_by_slug(slug, rule_set_id=rule_set_id, language_code=language_code)
    if projection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return projection
