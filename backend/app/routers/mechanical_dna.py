from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.mechanical_dna import MechanicalDNAResponse
from app.services.mechanical_dna import MechanicalDNAService

router = APIRouter()


def get_mechanical_dna_service() -> MechanicalDNAService:
    return MechanicalDNAService()


@router.get("/games/{slug}/connections", response_model=MechanicalDNAResponse)
async def get_game_connections(
    slug: str,
    limit: int = Query(default=8, ge=1, le=30),
    service: MechanicalDNAService = Depends(get_mechanical_dna_service),
):
    result = await service.get_connections(slug, limit=limit)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return result
