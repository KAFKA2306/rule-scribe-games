from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import GameDetail, GameUpdate


MIGRATIONS = Path(__file__).resolve().parents[1] / "app/db/migrations"
MIGRATION_007 = MIGRATIONS / "007_catalog_acl_trust_and_strict_slug.sql"
MIGRATION_008 = MIGRATIONS / "008_validate_games_slug.sql"
MIGRATION_009 = MIGRATIONS / "009_remove_legacy_trust.sql"


def test_game_api_exposes_separate_trust_axes_without_legacy_official_fields():
    game = GameDetail(
        id="game-1",
        slug="example",
        title="Example",
        identity_status="verified",
        source_url="https://publisher.example/game",
        source_trust="official_publisher",
        content_review_status="human_reviewed",
    )
    payload = game.model_dump()

    assert payload["source_trust"] == "official_publisher"
    assert payload["content_review_status"] == "human_reviewed"
    assert "is_official" not in GameDetail.model_fields
    assert "official_url" not in GameDetail.model_fields


def test_trust_enums_fail_closed_on_unknown_values():
    with pytest.raises(ValidationError):
        GameDetail(id="game-1", title="Example", source_trust="official")
    with pytest.raises(ValidationError):
        GameUpdate(content_review_status="approved")


def test_catalog_schema_separates_compatible_rollout_slug_validation_and_trust_cleanup():
    additive_sql = MIGRATION_007.read_text(encoding="utf-8")
    slug_sql = MIGRATION_008.read_text(encoding="utf-8")
    cleanup_sql = MIGRATION_009.read_text(encoding="utf-8")

    assert "ADD COLUMN IF NOT EXISTS source_trust" in additive_sql
    assert "ADD COLUMN IF NOT EXISTS content_review_status" in additive_sql
    assert "SET source_url = g.official_url" in additive_sql
    assert "existing.source_url = g.official_url" in additive_sql
    assert "legacy.official_url = g.official_url" in additive_sql
    assert "DROP COLUMN IF EXISTS is_official" not in additive_sql
    assert "DROP COLUMN IF EXISTS official_url" not in additive_sql

    assert "VALIDATE CONSTRAINT games_slug_required" in slug_sql
    assert "DROP COLUMN" not in slug_sql

    assert "DROP COLUMN IF EXISTS is_official" in cleanup_sql
    assert "DROP COLUMN IF EXISTS official_url" in cleanup_sql
    assert "games_slug_required" not in cleanup_sql


def test_catalog_acl_tables_are_rls_protected_and_match_production_contract():
    sql = MIGRATION_007.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS public.catalog_editors" in sql
    assert "role IN ('owner', 'editor')" in sql
    assert "active boolean NOT NULL DEFAULT true" in sql
    assert "ALTER TABLE public.catalog_editors ENABLE ROW LEVEL SECURITY" in sql
    assert "CREATE TABLE IF NOT EXISTS public.catalog_mutation_audit" in sql
    assert "actor_user_id" in sql
    assert "game_slug" in sql
    assert "outcome" in sql
    assert "ALTER TABLE public.catalog_mutation_audit ENABLE ROW LEVEL SECURITY" in sql
