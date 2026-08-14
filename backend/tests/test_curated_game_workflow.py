from pathlib import Path

import pytest

from app.scripts.curated_game_workflow import (
    GENERATED_GUIDES_PATH,
    WorkflowError,
    load_all_specs,
    load_spec,
    plan_identity,
    render_generated_registry,
    validate_assertions,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SKULL_KING = REPO_ROOT / "data" / "curated-games" / "skull-king.json"


def test_skull_king_replays_from_structured_input_without_semantic_diff():
    spec = load_spec(SKULL_KING)
    validate_assertions(spec)

    assert spec.slug == "skull-king"
    assert spec.source.url == "https://www.grandpabecksgames.com/pages/skull-king"
    assert spec.source.revision == "grandpa-becks-current-rulebook-accessed-2026-08-14"
    assert spec.guide["facts"]["rounds"] == 10
    assert spec.guide["scoring"]["summary"].find("配札枚数×10点") >= 0
    assert render_generated_registry(load_all_specs()) == GENERATED_GUIDES_PATH.read_text(encoding="utf-8")


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
                    "language_code": None,
                }
            ],
        )
