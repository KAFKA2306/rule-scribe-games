from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import games


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


def test_authenticated_regeneration_uses_existing_slug_update_path():
    service = MutableGameService()
    app = _app_with_service(service)
    app.dependency_overrides[games.get_current_user] = lambda: {"id": "user-1"}
    client = TestClient(app)

    response = client.patch("/api/games/example?regenerate=true&fill_missing_only=true")

    assert response.status_code == 200
    assert response.json()["slug"] == "example"
    assert service.updated is True


def test_post_search_checks_database_before_generation():
    service = DBFirstService()
    client = TestClient(_app_with_service(service))

    response = client.post("/api/search", json={"query": "レラティブ・スペース", "generate": True})

    assert response.status_code == 200
    assert response.json()[0]["slug"] == "existing"
    assert service.created is False
