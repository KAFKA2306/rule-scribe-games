from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import games
from app.services import rulesets, seo_renderer
from app.services.rulesets import RuleSetReadError, RuleSetService


async def _known_game(_slug: str):
    return {"id": "game-1", "slug": "example"}


@pytest.mark.asyncio
async def test_ruleset_zero_rows_remains_not_available(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(rulesets.supabase, "get_by_slug", _known_game)
    monkeypatch.setattr(rulesets.supabase, "is_local", lambda: False)
    monkeypatch.setattr(RuleSetService, "_load_rulesets", staticmethod(lambda _game: []))

    result = await RuleSetService().get_by_slug("example")

    assert result is not None
    assert result.status == "not_available"
    assert result.rulesets == []


@pytest.mark.asyncio
async def test_ruleset_transient_read_failure_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch):
    attempts = 0

    def load(_game):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.RemoteProtocolError("temporary disconnect")
        return [
            {
                "id": "set-1",
                "game_id": "game-1",
                "version": 1,
                "language_code": "ja",
                "status": "active",
                "verification_status": "source_bound",
                "is_active": True,
            }
        ]

    monkeypatch.setattr(rulesets.supabase, "get_by_slug", _known_game)
    monkeypatch.setattr(rulesets.supabase, "is_local", lambda: False)
    monkeypatch.setattr(RuleSetService, "_load_rulesets", staticmethod(load))

    result = await RuleSetService().get_by_slug("example")

    assert attempts == 2
    assert result is not None
    assert result.status == "available"
    assert result.rulesets[0].ruleset_id == "set-1"


@pytest.mark.asyncio
async def test_ruleset_terminal_read_failure_is_repeatably_fail_visible(monkeypatch: pytest.MonkeyPatch):
    attempts = 0

    def fail(_game):
        nonlocal attempts
        attempts += 1
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(rulesets.supabase, "get_by_slug", _known_game)
    monkeypatch.setattr(rulesets.supabase, "is_local", lambda: False)
    monkeypatch.setattr(RuleSetService, "_load_rulesets", staticmethod(fail))

    for _ in range(2):
        with pytest.raises(RuleSetReadError, match="ruleset backend failure"):
            await RuleSetService().get_by_slug("example")

    assert attempts == 2


class FailingRuleSetService:
    async def get_by_slug(self, _slug: str):
        raise RuleSetReadError("ruleset backend failure for example")


def test_ruleset_route_does_not_convert_backend_failure_to_not_available():
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_ruleset_service] = lambda: FailingRuleSetService()
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/games/example/rule-sets")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_canonical_rule_text_propagates_ruleset_read_failure(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(seo_renderer, "RuleSetService", FailingRuleSetService)

    with pytest.raises(RuleSetReadError):
        await seo_renderer._canonical_rule_text("example")


class PublicGameService:
    async def get_game_by_slug(self, slug: str):
        return {
            "id": "game-1",
            "slug": slug,
            "title": "Example",
            "work_id": "work-1",
            "structured_data": {},
        }


def test_game_route_does_not_silently_fallback_when_canonical_rules_cannot_be_read(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fail(_slug: str):
        raise RuleSetReadError("ruleset backend failure for example")

    monkeypatch.setattr(games, "_canonical_rule_text", fail)
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_game_service] = lambda: PublicGameService()
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/games/example")

    assert response.status_code == 500
