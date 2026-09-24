import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models.ruleset import RuleSetListResponse
from app.routers import games
from app.services import rulesets as ruleset_module
from app.services.rulesets import RuleSetReadError, RuleSetService
from app.services.seo_renderer import _canonical_rule_text


async def _async_value(value):
    return value


@pytest.mark.anyio
async def test_ruleset_service_keeps_zero_rows_as_not_available(monkeypatch):
    monkeypatch.setattr(ruleset_module.supabase, "get_by_slug", lambda slug: _async_value({"id": "game-1", "slug": slug}))
    monkeypatch.setattr(ruleset_module.supabase, "is_local", lambda: False)
    monkeypatch.setattr(RuleSetService, "_load_rulesets", staticmethod(lambda game: []))

    result = await RuleSetService().get_by_slug("example")

    assert result == RuleSetListResponse(status="not_available", game_id="game-1", slug="example")


@pytest.mark.anyio
async def test_ruleset_service_propagates_terminal_backend_failure_repeatedly(monkeypatch):
    monkeypatch.setattr(ruleset_module.supabase, "get_by_slug", lambda slug: _async_value({"id": "game-1", "slug": slug}))
    monkeypatch.setattr(ruleset_module.supabase, "is_local", lambda: False)

    def fail(_game):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(RuleSetService, "_load_rulesets", staticmethod(fail))

    for _ in range(2):
        with pytest.raises(RuleSetReadError, match="RuleSet canonical read failed"):
            await RuleSetService().get_by_slug("example")


@pytest.mark.anyio
async def test_canonical_rule_text_does_not_collapse_read_failure(monkeypatch):
    async def fail(_self, _slug):
        raise RuleSetReadError("database unavailable")

    monkeypatch.setattr(RuleSetService, "get_by_slug", fail)

    with pytest.raises(RuleSetReadError):
        await _canonical_rule_text("example")


class FailingRuleSetService:
    async def get_by_slug(self, _slug: str):
        raise RuleSetReadError("database unavailable")


def test_ruleset_api_does_not_return_200_not_available_on_backend_failure():
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_ruleset_service] = lambda: FailingRuleSetService()
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/games/example/rule-sets")

    assert response.status_code >= 500
