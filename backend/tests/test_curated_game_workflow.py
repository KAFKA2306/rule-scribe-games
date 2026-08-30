from pathlib import Path

import pytest

from app.scripts.curated_game_workflow import (
    LEGACY_RULE_FIELDS,
    WorkflowError,
    load_spec,
    plan_identity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SKULL_KING = REPO_ROOT / "data" / "curated-games" / "skull-king.json"


def test_skull_king_replays_from_structured_catalog_input_without_rule_authority():
    spec = load_spec(SKULL_KING)

    assert spec.slug == "skull-king"
    assert spec.source.url == "https://www.grandpabecksgames.com/pages/skull-king"
    assert spec.source.revision == "grandpa-becks-current-en-rulebook-faq-accessed-2026-08-22"
    assert all(field not in spec.game for field in LEGACY_RULE_FIELDS)
    assert "guide" not in spec.model_fields
    assert "assertions" not in spec.model_fields


def test_existing_slug_for_same_work_is_idempotent_update():
    spec = load_spec(SKULL_KING)
    plan = plan_identity(
        spec,
        slug_rows=[{"id": "game-1", "work_id": "work-1"}],
        work_rows=[{"id": "work-1", "canonical_title": "Skull King"}],
        edition_rows=[{"id": "game-1", "slug": "skull-king"}],
    )

    assert plan.game_id == "game-1"
    assert plan.work_id == "work-1"
    assert plan.create_work is False


def test_exact_slug_disambiguates_duplicate_canonical_titles():
    spec = load_spec(SKULL_KING)
    plan = plan_identity(
        spec,
        slug_rows=[{"id": "game-1", "work_id": "work-2"}],
        work_rows=[
            {"id": "work-1", "canonical_title": "Skull King"},
            {"id": "work-2", "canonical_title": "Skull King"},
        ],
        edition_rows=[],
    )

    assert plan.game_id == "game-1"
    assert plan.work_id == "work-2"
    assert plan.create_work is False


def test_duplicate_canonical_titles_without_exact_slug_fail_closed():
    spec = load_spec(SKULL_KING)
    with pytest.raises(WorkflowError, match="multiple canonical works"):
        plan_identity(
            spec,
            slug_rows=[],
            work_rows=[
                {"id": "work-1", "canonical_title": "Skull King"},
                {"id": "work-2", "canonical_title": "Skull King"},
            ],
            edition_rows=[],
        )


def test_slug_collision_with_different_work_fails_before_write():
    spec = load_spec(SKULL_KING)
    with pytest.raises(WorkflowError, match="different canonical work"):
        plan_identity(
            spec,
            slug_rows=[{"id": "game-1", "work_id": "other-work"}],
            work_rows=[{"id": "work-1", "canonical_title": "Skull King"}],
            edition_rows=[],
        )


def test_duplicate_work_edition_under_another_slug_fails_before_write():
    spec = load_spec(SKULL_KING)
    with pytest.raises(WorkflowError, match="refusing duplicate"):
        plan_identity(
            spec,
            slug_rows=[],
            work_rows=[{"id": "work-1", "canonical_title": "Skull King"}],
            edition_rows=[
                {
                    "id": "game-2",
                    "slug": "skull-king-copy",
                    "edition_label": "Grandpa Beck's Games current edition",
                    "language_code": "en",
                }
            ],
        )
