from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import games


class MissingGameService:
    async def get_game_by_slug(self, slug: str):
        return None


class MutableGameService:
    def __init__(self):
        self.updated = False
        self.last_updates = None

    async def update_game_content(self, slug: str, fill_missing_only: bool = False):
        self.updated = True
        return {"id": "game-1", "slug": slug, "title": "Example", "work_id": "work-1"}

    async def update_game_manual(self, slug: str, updates: dict):
        self.updated = True
        self.last_updates = updates
        return {"id": "game-1", "slug": slug, "title": updates.get("title", "Example")}


class NotFoundMutableGameService(MutableGameService):
    async def update_game_manual(self, slug: str, updates: dict):
        raise ValueError("missing")


class DBFirstService:
    def __init__(self):
        self.created = False

    async def search_games(self, query: str):
        return [{"id": "game-1", "slug": "existing", "title": "既存ゲーム", "title_ja": query}]

    async def create_game_from_query(self, query: str):
        self.created = True
        return {"id": "game-2", "slug": "generated", "title": query}


def _app_with_service(service):
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_game_service] = lambda: service
    return app


def _install_editor_authorization(app, monkeypatch, role="editor"):
    app.dependency_overrides[games.get_current_user] = lambda: {"id": "user-1"}

    async def get_role(_user_id: str):
        return role

    async def audit(**_kwargs):
        return None

    monkeypatch.setattr(games.catalog_authorization, "get_catalog_editor_role", get_role)
    monkeypatch.setattr(games.catalog_authorization, "record_catalog_mutation_audit", audit)


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


def test_regular_authenticated_user_cannot_mutate_global_catalog(monkeypatch):
    service = MutableGameService()
    app = _app_with_service(service)
    _install_editor_authorization(app, monkeypatch, role=None)
    client = TestClient(app)

    response = client.patch("/api/games/example", json={"title": "Should not write"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Catalog editor permission required"
    assert service.updated is False


def test_authorized_editor_regeneration_uses_existing_slug_update_path(monkeypatch):
    service = MutableGameService()
    app = _app_with_service(service)
    _install_editor_authorization(app, monkeypatch, role="editor")
    client = TestClient(app)

    response = client.patch("/api/games/example?regenerate=true&fill_missing_only=true")

    assert response.status_code == 200
    assert response.json()["slug"] == "example"
    assert service.updated is True


def test_identity_fields_are_not_forwarded_to_manual_update(monkeypatch):
    service = MutableGameService()
    app = _app_with_service(service)
    _install_editor_authorization(app, monkeypatch, role="editor")
    client = TestClient(app)

    response = client.patch(
        "/api/games/example",
        json={"slug": "hijacked", "id": "other-id", "work_id": "other-work", "identity_status": "official", "title": "Safe title"},
    )

    assert response.status_code == 200
    assert service.updated is True
    assert service.last_updates == {"title": "Safe title"}


def test_authorized_editor_missing_slug_returns_404(monkeypatch):
    service = NotFoundMutableGameService()
    app = _app_with_service(service)
    _install_editor_authorization(app, monkeypatch, role="editor")
    client = TestClient(app)

    response = client.patch("/api/games/missing", json={"title": "No target"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}


def test_post_search_checks_database_before_generation():
    service = DBFirstService()
    client = TestClient(_app_with_service(service))

    response = client.post("/api/search", json={"query": "レラティブ・スペース", "generate": True})

    assert response.status_code == 200
    assert response.json()[0]["slug"] == "existing"
    assert service.created is False
