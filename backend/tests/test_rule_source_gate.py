import pytest

from app.services import game_service


@pytest.fixture
def generated_payload():
    return {
        "title": "Example Game",
        "title_ja": "サンプルゲーム",
        "summary": "summary",
        "description": "description",
        "min_players": 2,
        "max_players": 4,
        "play_time": 30,
        "min_age": 10,
        "bga_url": "https://boardgamearena.com/gamepanel?game=example",
        "rules_content": "invented rule text",
        "structured_data": {
            "keywords": [{"term": "推測", "description": "unsupported"}],
            "key_elements": [],
            "mechanics": ["Unknown"],
            "best_player_count": "4",
        },
    }


@pytest.mark.asyncio
async def test_unsourced_generation_discards_rule_derived_fields(monkeypatch, generated_payload):
    async def fake_generate(*_args, **_kwargs):
        return generated_payload

    monkeypatch.setattr(game_service._gemini, "generate_structured_json", fake_generate)
    monkeypatch.setattr(game_service._key_rotator, "keys", ["test-key"])
    monkeypatch.setattr(game_service._key_rotator, "get_next_key", lambda: "test-key")

    result = await game_service.generate_metadata("Example Game", context="DB summary only", source_bound=False)

    assert result["rules_content"] is None
    assert result["min_players"] is None
    assert result["max_players"] is None
    assert result["play_time"] is None
    assert result["min_age"] is None
    assert result["bga_url"] is None
    assert result["structured_data"]["keywords"] == []
    assert result["identity_status"] == "unverified"
    assert result["source_trust_status"] == "unknown"
    assert result["content_review_status"] == "ai_draft"
    assert result["is_official"] is False
    provenance = result["structured_data"]["generation_provenance"]
    assert provenance["source_bound"] is False
    assert provenance["content_review_status"] == "ai_draft"
    assert provenance["golden_version"] == "golden-v1"


@pytest.mark.asyncio
async def test_source_bound_generation_preserves_supported_rule_fields_without_promoting_trust(monkeypatch, generated_payload):
    async def fake_generate(*_args, **_kwargs):
        return generated_payload

    monkeypatch.setattr(game_service._gemini, "generate_structured_json", fake_generate)
    monkeypatch.setattr(game_service._key_rotator, "keys", ["test-key"])
    monkeypatch.setattr(game_service._key_rotator, "get_next_key", lambda: "test-key")

    result = await game_service.generate_metadata(
        "Example Game",
        context="Verified rule text supplied by a source extractor",
        source_bound=True,
    )

    assert result["rules_content"] == "invented rule text"
    assert result["min_players"] == 2
    assert result["bga_url"] == "https://boardgamearena.com/gamepanel?game=example"
    assert result["source_trust_status"] == "unknown"
    assert result["content_review_status"] == "ai_draft"
    assert result["is_official"] is False
    assert result["structured_data"]["generation_provenance"]["source_bound"] is True


def test_regeneration_merge_never_erases_existing_verified_fields_with_null():
    original = {"rules_content": "verified rules", "min_players": 2, "summary": "old"}
    incoming = {"rules_content": None, "min_players": None, "summary": "new"}
    merged = game_service._merge_fields(original, incoming, fill_missing_only=False)
    assert merged["rules_content"] == "verified rules"
    assert merged["min_players"] == 2
    assert merged["summary"] == "new"
