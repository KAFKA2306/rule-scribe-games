import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.models.evidence import ClaimTarget, EvidenceTraceResponse
from app.routers import games
from app.services.evidence import EvidenceService


@pytest.mark.parametrize(
    ("target_type", "kwargs"),
    [
        ("component", {"component_id": "card.scout"}),
        ("component_set", {"component_set_id": "cards"}),
        ("property_definition", {"property_key": "cost"}),
    ],
)
def test_component_catalog_targets_have_first_class_shapes(target_type, kwargs):
    target = ClaimTarget(target_type=target_type, **kwargs)
    assert target.target_type.value == target_type
    for key, value in kwargs.items():
        assert getattr(target, key) == value


def test_component_catalog_targets_reject_mixed_shapes():
    with pytest.raises(ValidationError):
        ClaimTarget(target_type="component", component_id="card.scout", property_key="cost")
    with pytest.raises(ValidationError):
        ClaimTarget(target_type="component_set", component_set_id="cards", component_id="card.scout")
    with pytest.raises(ValidationError):
        ClaimTarget(target_type="property_definition", property_key="cost", ordinal=0)


def test_evidence_service_reconstructs_component_set_target_from_db_row():
    claim = EvidenceService._claim_model(
        {
            "claim_id": "claim.component-set.cards",
            "rule_set_id": "ruleset-1",
            "claim_type": "component_set",
            "normalized_payload": {"canonical_name": "Cards"},
            "target_type": "component_set",
            "component_set_id": "cards",
            "lifecycle_status": "accepted",
            "generator_provenance": {},
        }
    )
    assert claim.target.component_set_id == "cards"
    assert claim.target.component_id is None
    assert claim.target.property_key is None


class FakeEvidenceTargetService:
    async def get_trace(self, slug, ruleset_id, target):
        return EvidenceTraceResponse(
            status="not_available",
            game_id="game-1",
            slug=slug,
            ruleset_id=ruleset_id,
            target=target,
            claims=[],
        )

    async def get_claim(self, slug, ruleset_id, claim_id):
        return None


def _app():
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_evidence_service] = FakeEvidenceTargetService
    return app


def test_evidence_api_accepts_component_set_target():
    response = TestClient(_app()).get(
        "/api/games/yro/evidence",
        params={
            "rule_set_id": "ruleset-1",
            "target_type": "component_set",
            "component_set_id": "adventurers",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["target"]["component_set_id"] == "adventurers"


def test_evidence_api_rejects_component_set_target_without_component_set_id():
    response = TestClient(_app()).get(
        "/api/games/yro/evidence",
        params={"rule_set_id": "ruleset-1", "target_type": "component_set"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
