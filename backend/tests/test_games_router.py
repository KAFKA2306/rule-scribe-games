import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app as production_app
from app.routers import games
from app.services.game_service import GameService, UnverifiedGameIdentityError


class MissingGameService:
    async def get_game_by_slug(self, slug: str):
        return None


class MutableGameService:
    def __init__(self):
        self.updated = False

    async def update_game_content(self, slug: str, fill_missing_only: bool = False):
        self.updated = True
        return {"id": "game-1", "slug": slug, "title": "Example", "work_id": "work-1"}

    async def update_game_manual(self, slug: str, updates: dict):
        self.updated = True
        return {"id": "game-1", "slug": slug, "title": updates.get("title", "Example")}


class UnverifiedRegenerationService:
    async def update_game_content(self, slug: str, fill_missing_only: bool = False):
        raise UnverifiedGameIdentityError("Game identity must be verified before content regeneration")


class DBFirstService:
    def __init__(self):
        self.created = False

    async def search_games(self, query: str):
        return [{"id": "game-1", "slug": "existing", "title": "既存ゲーム", "title_ja": query}]

    async def create_game_from_query(self, query: str):
        self.created = True
        return {"id": "game-2", "slug": "generated", "title": query}


class PublicReadService:
    async def get_game_by_slug(self, slug: str):
        return {"id": "game-1", "slug": slug, "title": "Example", "work_id": "work-1"}

    async def list_recent_games(self, limit: int, offset: int):
        return {
            "data": [{"id": "game-1", "slug": "example", "title": "Example", "work_id": "work-1"}],
            "total": 1,
        }


def _app_with_service(service):
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_game_service] = lambda: service
    return app


def test_missing_game_slug_returns_404_instead_of_response_validation_500():
    client = TestClient(_app_with_service(MissingGameService()))
    response = client.get("/api/games/ipso")

    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}


def test_catalog_patch_requires_authentication_before_mutation():
    service = MutableGameService()
    client = TestClient(_app_with_service(service))

    response = client.patch("/api/games/example?regenerate=true")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"
    assert service.updated is False


def test_authorized_regeneration_uses_existing_slug_update_path():
    service = MutableGameService()
    app = _app_with_service(service)
    app.dependency_overrides[games.require_catalog_editor] = lambda: {
        "id": "editor-1",
        "catalog_role": "editor",
    }
    client = TestClient(app)

    response = client.patch("/api/games/example?regenerate=true&fill_missing_only=true")

    assert response.status_code == 200
    assert response.json()["slug"] == "example"
    assert service.updated is True


def test_authorized_regeneration_reports_unverified_identity_conflict():
    app = _app_with_service(UnverifiedRegenerationService())
    app.dependency_overrides[games.require_catalog_editor] = lambda: {
        "id": "editor-1",
        "catalog_role": "editor",
    }
    client = TestClient(app)

    response = client.patch("/api/games/game?regenerate=true")

    assert response.status_code == 409
    assert response.json() == {"detail": "Game identity must be verified before content regeneration"}


@pytest.mark.asyncio
async def test_regeneration_rejects_unverified_identity_before_generation(monkeypatch):
    async def get_unverified_game(slug: str):
        return {
            "id": "mixed-game",
            "slug": slug,
            "title": "ワインと毒とゴブレット",
            "title_ja": "みんなでぽんこつペイント",
            "summary": "mixed identity fixture",
            "identity_status": "unverified",
        }

    async def unexpected_generation(*args, **kwargs):
        raise AssertionError("generation must not run for an unverified identity")

    monkeypatch.setattr("app.services.game_service.supabase.get_by_slug", get_unverified_game)
    monkeypatch.setattr("app.services.game_service.generate_metadata", unexpected_generation)
    service = object.__new__(GameService)

    with pytest.raises(UnverifiedGameIdentityError, match="identity must be verified"):
        await service.update_game_content("game")


def test_authorized_manual_update_does_not_accept_identity_fields():
    service = MutableGameService()
    app = _app_with_service(service)
    app.dependency_overrides[games.require_catalog_editor] = lambda: {
        "id": "editor-1",
        "catalog_role": "admin",
    }
    client = TestClient(app)

    response = client.patch(
        "/api/games/example",
        json={"title": "Updated", "slug": "attacker-slug", "work_id": "attacker-work"},
    )

    assert response.status_code == 200
    assert response.json()["slug"] == "example"
    assert response.json()["title"] == "Updated"
    assert service.updated is True


def test_post_search_rejects_legacy_generation_request_before_any_write():
    service = DBFirstService()
    client = TestClient(_app_with_service(service))

    response = client.post("/api/search", json={"query": "レラティブ・スペース", "generate": True})

    assert response.status_code == 403
    assert response.json()["detail"] == "Catalog generation is not available from public search"
    assert service.created is False


def test_post_search_remains_read_only_for_legacy_clients():
    service = DBFirstService()
    client = TestClient(_app_with_service(service))

    response = client.post("/api/search", json={"query": "レラティブ・スペース", "generate": False})

    assert response.status_code == 200
    assert response.json()[0]["slug"] == "existing"
    assert service.created is False


def test_public_game_reads_use_standard_shared_cache_control():
    production_app.dependency_overrides[games.get_game_service] = lambda: PublicReadService()
    try:
        client = TestClient(production_app)

        detail = client.get("/api/games/example")
        listing = client.get("/api/games?limit=1&offset=0")

        for response in (detail, listing):
            assert response.status_code == 200
            assert response.headers["cache-control"] == "public, max-age=0, s-maxage=60, must-revalidate"
            assert "vercel-cdn-cache-control" not in response.headers
    finally:
        production_app.dependency_overrides.clear()


def test_cache_headers_do_not_apply_to_health_or_mutation_requests():
    production_app.dependency_overrides[games.get_game_service] = lambda: MutableGameService()
    try:
        client = TestClient(production_app)

        health = client.get("/api/health")
        patch = client.patch("/api/games/example?regenerate=true")

        assert "s-maxage" not in health.headers.get("cache-control", "")
        assert "s-maxage" not in patch.headers.get("cache-control", "")
    finally:
        production_app.dependency_overrides.clear()