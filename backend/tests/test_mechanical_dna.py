from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models.mechanical_dna import (
    MechanicalDNAConnection,
    MechanicalDNAResponse,
    SharedConcept,
)
from app.routers import mechanical_dna
from app.services.mechanical_dna import invert_hierarchy, jaccard_score


FRONTEND_GAME_PAGE = Path(__file__).parents[2] / "frontend" / "src" / "pages" / "GamePage.jsx"


def test_jaccard_rewards_more_exact_shared_concepts():
    source = {"a", "b", "c", "d"}
    one_shared = {"a", "x", "y"}
    three_shared = {"a", "b", "c", "x"}

    assert jaccard_score(source, three_shared) > jaccard_score(source, one_shared)
    assert jaccard_score(source, source) == 1.0
    assert jaccard_score(set(), source) == 0.0


def test_hierarchy_direction_is_inverted_from_source_perspective():
    assert invert_hierarchy("broader") == "narrower"
    assert invert_hierarchy("narrower") == "broader"


def test_response_contract_tracks_algorithm_version_and_stable_concept_ids():
    response = MechanicalDNAResponse(
        status="available",
        game_id="game-source",
        slug="source",
        connections=[
            MechanicalDNAConnection(
                game_id="game-target",
                slug="target",
                title="Target",
                rank=1,
                similarity_score=0.5,
                shared_concept_ids=["rule-pattern.trick"],
                shared_concepts=[
                    SharedConcept(
                        concept_id="rule-pattern.trick",
                        label="トリック",
                        language_code="ja",
                    )
                ],
            )
        ],
    )

    assert response.algorithm_version == "mechanical-dna-concept-v1"
    assert response.connections[0].shared_concept_ids == ["rule-pattern.trick"]


class FakeMechanicalDNAService:
    async def get_connections(self, slug: str, *, limit: int = 8):
        if slug == "missing":
            return None
        return MechanicalDNAResponse(
            status="available",
            game_id="game-source",
            slug=slug,
            connections=[],
        )


def app() -> FastAPI:
    instance = FastAPI()
    instance.include_router(mechanical_dna.router, prefix="/api")
    instance.dependency_overrides[mechanical_dna.get_mechanical_dna_service] = lambda: FakeMechanicalDNAService()
    return instance


def test_connections_api_has_available_empty_state_and_404_boundary():
    client = TestClient(app())

    response = client.get("/api/games/skull-king/connections?limit=8")
    assert response.status_code == 200
    assert response.json()["status"] == "available"
    assert response.json()["connections"] == []
    assert response.json()["algorithm_version"] == "mechanical-dna-concept-v1"

    assert client.get("/api/games/missing/connections").status_code == 404


def test_game_page_does_not_scan_first_50_games_or_match_legacy_mechanics_labels():
    source = FRONTEND_GAME_PAGE.read_text(encoding="utf-8")

    assert "/api/games?limit=50" not in source
    assert "mechanics?.includes(" not in source
    assert "structured_data?.mechanics" not in source
    assert "/connections?limit=8" in source
    assert "mechanical-dna-concept-v1" not in source  # version comes from the API response
