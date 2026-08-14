from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from app.models.ruleset import RuleSet, RuleSetListResponse
from app.routers import games


def _ruleset(**overrides):
    payload = {
        "ruleset_id": "set-physical-ja",
        "game_id": "game-1",
        "version": 1,
        "language_code": "ja",
        "edition_label": "base",
        "platform": "physical",
        "status": "active",
        "verification_status": "source_bound",
        "is_active": True,
    }
    payload.update(overrides)
    return RuleSet(**payload)


def test_ruleset_keeps_language_platform_and_revision_as_independent_axes():
    ruleset = _ruleset(revision_label="2026-08", source_revision="publisher-pdf-r2")

    assert ruleset.language_code == "ja"
    assert ruleset.platform == "physical"
    assert ruleset.revision_label == "2026-08"
    assert ruleset.source_revision == "publisher-pdf-r2"


def test_unknown_revision_is_preserved_without_inference():
    ruleset = _ruleset(revision_label=None, source_revision=None)
    assert ruleset.revision_label is None
    assert ruleset.source_revision is None


def test_variant_and_translation_relations_are_explicit():
    variant = _ruleset(
        ruleset_id="set-brutal",
        base_rule_set_id="set-base",
        relation_type="variant_of",
        variant_label="Brutal Mode",
    )
    translated = _ruleset(
        ruleset_id="set-en",
        language_code="en",
        base_rule_set_id="set-ja",
        relation_type="translation_of",
    )

    assert variant.relation_type.value == "variant_of"
    assert translated.relation_type.value == "translation_of"


def test_relation_requires_parent_and_variant_requires_label():
    with pytest.raises(ValidationError):
        _ruleset(relation_type="derived_from")

    with pytest.raises(ValidationError):
        _ruleset(base_rule_set_id="set-base", relation_type="variant_of", variant_label=None)


def test_superseded_ruleset_cannot_remain_active():
    with pytest.raises(ValidationError):
        _ruleset(status="superseded", is_active=True)


def test_ruleset_response_rejects_cross_game_mix():
    with pytest.raises(ValidationError):
        RuleSetListResponse(
            status="available",
            game_id="game-1",
            slug="example",
            rulesets=[_ruleset(game_id="game-2")],
        )


class FakeRuleSetService:
    async def get_by_slug(self, slug: str):
        if slug == "missing":
            return None
        return RuleSetListResponse(
            status="available",
            game_id="game-1",
            slug=slug,
            rulesets=[
                _ruleset(),
                _ruleset(
                    ruleset_id="set-bga-en",
                    language_code="en",
                    platform="boardgamearena",
                    edition_label="digital",
                ),
            ],
        )


def _app():
    app = FastAPI()
    app.include_router(games.router, prefix="/api")
    app.dependency_overrides[games.get_ruleset_service] = lambda: FakeRuleSetService()
    return app


def test_ruleset_api_lists_multiple_rulesets_for_one_game():
    client = TestClient(_app())
    response = client.get("/api/games/example/rule-sets")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "available"
    assert payload["game_id"] == "game-1"
    assert len(payload["rulesets"]) == 2
    assert {item["platform"] for item in payload["rulesets"]} == {"physical", "boardgamearena"}
    assert {item["language_code"] for item in payload["rulesets"]} == {"ja", "en"}


def test_ruleset_api_returns_404_only_for_unknown_game():
    client = TestClient(_app())
    response = client.get("/api/games/missing/rule-sets")
    assert response.status_code == 404
