from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app as production_app
from app.routers import games


class MissingGameService:
    async def get_game_by_slug(self, slug: str):
        return None


class MutableGameService:
    def __init__(self):
        self.updated = False

    async def update_game_manual(self, slug: str, updates: dict):
        self.updated = True
        return {"id": "game-1", "slug": slug, "title": updates.get("title", "Example")}


class PublicReadService:
    async def search_games(self, query: str):
        return [{"id": "game-1", "slug": "example", "title": "Example", "work_id": "work-1"}]

    async def get_game_by_slug(self, slug: str):
        return {
            "id": "game-1",
            "slug": slug,
            "title": "Example",
            "work_id": "work-1",
            "rules_content": "# Example\n\nDetailed player-facing rules.",
            "setup_summary": "Set up the example.",
            "gameplay_summary": "Take turns.",
            "end_game_summary": "Finish the example.",
            "structured_data": {
                "keywords": [],
                "key_elements": [],
                "mechanics": [],
                "best_player_count": None,
                "strategy_analysis": "Example strategy.",
                "persona_reviews": [
                    {"persona": "planner", "review_text": "Readable rules matter.", "rating": 8.0}
                ],
                "pro_tips": ["Example tip."],
                "rule_mistakes": ["Example mistake."],
            },
        }


async def _no_canonical_rules(_slug: str):
    return None


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


def test_game_detail_does_not_publish_legacy_rule_fields_without_canonical_rules(monkeypatch):
    monkeypatch.setattr(games, "_canonical_rule_text", _no_canonical_rules)
    client = TestClient(_app_with_service(PublicReadService()))

    detail = client.get("/api/games/example")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["rules_content"] is None
    assert payload["setup_summary"] is None
    assert payload["gameplay_summary"] is None
    assert payload["end_game_summary"] is None
    assert payload["structured_data"]["strategy_analysis"] == "Example strategy."
    assert payload["structured_data"]["persona_reviews"][0]["persona"] == "planner"

    search = client.get("/api/search?q=example")
    assert search.status_code == 200
    assert "rules_content" not in search.json()[0]


def test_catalog_patch_requires_authentication_before_mutation():
    service = MutableGameService()
    client = TestClient(_app_with_service(service))

    response = client.patch("/api/games/example", json={"title": "Updated"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"
    assert service.updated is False


def test_catalog_patch_rejects_deprecated_rule_row_fields_before_mutation():
    service = MutableGameService()
    app = _app_with_service(service)
    app.dependency_overrides[games.require_catalog_editor] = lambda: {
        "id": "editor-1",
        "catalog_role": "editor",
    }
    client = TestClient(app)

    response = client.patch("/api/games/example", json={"rules_content": "unverified legacy rule"})

    assert response.status_code == 422
    assert service.updated is False


def test_read_only_search_remains_and_legacy_post_search_is_removed():
    client = TestClient(_app_with_service(PublicReadService()))

    get_response = client.get("/api/search?q=example")
    assert get_response.status_code == 200
    assert get_response.json()[0]["slug"] == "example"
    assert client.post("/api/search", json={"query": "example", "generate": True}).status_code == 405


def test_legacy_regeneration_request_has_no_mutation_contract():
    service = MutableGameService()
    app = _app_with_service(service)
    app.dependency_overrides[games.require_catalog_editor] = lambda: {
        "id": "editor-1",
        "catalog_role": "editor",
    }
    client = TestClient(app)

    response = client.patch("/api/games/example?regenerate=true")

    assert response.status_code == 422
    assert service.updated is False


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


def test_directory_query_parameters_are_forwarded(monkeypatch):
    captured = {}

    async def fake_directory_query(**kwargs):
        captured.update(kwargs)
        return {"data": [], "total": 7}

    monkeypatch.setattr(games, "list_directory_games", fake_directory_query)
    client = TestClient(_app_with_service(PublicReadService()))

    response = client.get(
        "/api/games?q=alpha&players=3&time=30-60&tier=A&sort=year&limit=10&offset=20"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 7
    assert captured == {
        "q": "alpha",
        "players": "3",
        "time_filter": "30-60",
        "tier": "A",
        "sort": "year",
        "limit": 10,
        "offset": 20,
    }


def test_public_game_reads_use_browser_and_cdn_cache_control(monkeypatch):
    async def fake_directory_query(**kwargs):
        return {
            "data": [{"id": "game-1", "slug": "example", "title": "Example", "work_id": "work-1"}],
            "total": 1,
        }

    monkeypatch.setattr(games, "list_directory_games", fake_directory_query)
    monkeypatch.setattr(games, "_canonical_rule_text", _no_canonical_rules)
    production_app.dependency_overrides[games.get_game_service] = lambda: PublicReadService()
    try:
        client = TestClient(production_app)

        detail = client.get("/api/games/example")
        listing = client.get("/api/games?limit=1&offset=0")

        for response in (detail, listing):
            assert response.status_code == 200
            assert response.headers["cache-control"] == "public, max-age=0, must-revalidate"
            assert response.headers["cdn-cache-control"] == "public, max-age=60, stale-while-revalidate=300"
    finally:
        production_app.dependency_overrides.clear()


def test_cache_headers_do_not_apply_to_health_mutation_or_missing_game():
    production_app.dependency_overrides[games.get_game_service] = lambda: MissingGameService()
    try:
        client = TestClient(production_app)

        health = client.get("/api/health")
        patch = client.patch("/api/games/example", json={"title": "Updated"})
        missing = client.get("/api/games/not-found")

        for response in (health, patch, missing):
            assert "cdn-cache-control" not in response.headers
    finally:
        production_app.dependency_overrides.clear()
