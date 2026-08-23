from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import games


class LegacyBackedGameService:
    async def get_game_by_slug(self, slug: str):
        return {
            "id": "game-1",
            "slug": slug,
            "title": "Example",
            "work_id": "work-1",
            "rules_content": "legacy rule text",
        }


def test_detail_api_prefers_canonical_projection_over_legacy_rules(monkeypatch):
    async def canonical_rule_text(slug: str):
        assert slug == "example"
        return "## セットアップ\n- source-backed canonical rule"

    monkeypatch.setattr(games, "_canonical_rule_text", canonical_rule_text)
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_game_service] = lambda: LegacyBackedGameService()

    response = TestClient(app).get("/api/games/example")

    assert response.status_code == 200
    assert response.json()["rules_content"] == "## セットアップ\n- source-backed canonical rule"


def test_detail_api_keeps_legacy_rules_when_canonical_projection_is_unavailable(monkeypatch):
    async def canonical_rule_text(slug: str):
        return None

    monkeypatch.setattr(games, "_canonical_rule_text", canonical_rule_text)
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_game_service] = lambda: LegacyBackedGameService()

    response = TestClient(app).get("/api/games/example")

    assert response.status_code == 200
    assert response.json()["rules_content"] == "legacy rule text"
