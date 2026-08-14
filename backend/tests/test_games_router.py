from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import games


class MissingGameService:
    async def get_game_by_slug(self, slug: str):
        return None


def test_missing_game_slug_returns_404_instead_of_response_validation_500():
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_game_service] = lambda: MissingGameService()

    client = TestClient(app)
    response = client.get("/api/games/ipso")

    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}
