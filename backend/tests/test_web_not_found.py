from fastapi.testclient import TestClient

from app import main


def test_missing_web_game_returns_user_facing_html_404(monkeypatch):
    async def missing(_slug: str):
        return None

    monkeypatch.setattr(main, "generate_seo_html", missing)
    client = TestClient(main.app)

    response = client.get("/games/not-a-real-game")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
    assert "ゲームが見つかりません" in response.text
    assert "ゲーム一覧へ戻る" in response.text
    assert 'name="robots" content="noindex, nofollow"' in response.text
    assert 'rel="canonical"' not in response.text
    assert 'application/json' not in response.headers["content-type"]


def test_valid_web_game_keeps_rendered_html_200(monkeypatch):
    async def rendered(_slug: str):
        return "<!doctype html><html><head><title>Known Game</title></head><body><h1>Known Game</h1></body></html>"

    monkeypatch.setattr(main, "generate_seo_html", rendered)
    client = TestClient(main.app)

    response = client.get("/games/known-game")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Known Game" in response.text
