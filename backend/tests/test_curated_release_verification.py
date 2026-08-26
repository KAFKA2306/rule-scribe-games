import pytest

from app.scripts.curated_game_workflow import WorkflowError
from app.scripts.curated_release_verification import (
    release_catalog_contract,
    validate_release_catalog_fields,
)


def test_release_contract_excludes_mutable_player_content_and_legacy_source_url():
    contract = release_catalog_contract(
        {
            "slug": "game",
            "title": "Game",
            "source_url": "https://publisher.example/rules",
            "identity_source": "https://publisher.example/products/game",
            "identity_status": "verified",
            "description": "old description",
            "summary": "old summary",
            "rules_content": "old rules",
            "setup_summary": "old setup",
            "gameplay_summary": "old gameplay",
            "end_game_summary": "old end",
            "structured_data": {"rule_mistakes": ["old"]},
            "content_review_status": "ai_draft",
        }
    )

    assert contract == {
        "slug": "game",
        "title": "Game",
        "identity_source": "https://publisher.example/products/game",
        "identity_status": "verified",
    }


def test_source_bound_rulebook_provenance_can_move_without_release_failure():
    expected = {
        "slug": "game",
        "title": "Game",
        "source_url": "https://publisher.example/rules.pdf",
        "identity_source": "https://publisher.example/products/game",
        "identity_status": "verified",
        "description": "curated description",
        "rules_content": "curated legacy rules",
        "content_review_status": "ai_draft",
    }
    production = {
        "slug": "game",
        "title": "Game",
        "source_url": "https://publisher.example/products/game",
        "identity_source": "https://publisher.example/products/game",
        "identity_status": "verified",
        "description": "source-bound description",
        "rules_content": None,
        "content_review_status": "human_reviewed",
    }

    validate_release_catalog_fields(expected, production)


def test_identity_drift_still_fails_release_verification():
    expected = {
        "slug": "game",
        "title": "Game",
        "source_url": "https://publisher.example/rules.pdf",
        "identity_source": "https://publisher.example/products/game",
        "identity_status": "verified",
    }
    production = {
        "slug": "game",
        "title": "Different Game",
        "source_url": "https://publisher.example/products/game",
        "identity_source": "https://publisher.example/products/game",
        "identity_status": "verified",
    }

    with pytest.raises(WorkflowError, match="game.title"):
        validate_release_catalog_fields(expected, production)


def test_identity_source_drift_still_fails_release_verification():
    expected = {
        "slug": "game",
        "title": "Game",
        "identity_source": "https://publisher.example/products/game",
        "identity_status": "verified",
    }
    production = {
        "slug": "game",
        "title": "Game",
        "identity_source": "https://other.example/game",
        "identity_status": "verified",
    }

    with pytest.raises(WorkflowError, match="game.identity_source"):
        validate_release_catalog_fields(expected, production)
