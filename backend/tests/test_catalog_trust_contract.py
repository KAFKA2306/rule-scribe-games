from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import GameDetail, GameUpdate


MIGRATION = Path("backend/app/db/migrations/007_catalog_acl_trust_and_strict_slug.sql")


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


def test_catalog_schema_removes_ambiguous_legacy_trust_and_validates_slug():
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "ADD COLUMN IF NOT EXISTS source_trust" in sql
    assert "ADD COLUMN IF NOT EXISTS content_review_status" in sql
    assert "SET source_url = official_url" in sql
    assert "DROP COLUMN IF EXISTS is_official" in sql
    assert "DROP COLUMN IF EXISTS official_url" in sql
    assert "CHECK (slug IS NOT NULL AND btrim(slug) <> '')" in sql
    assert "NOT VALID" not in sql


def test_catalog_acl_tables_are_rls_protected():
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS public.catalog_editors" in sql
    assert "ALTER TABLE public.catalog_editors ENABLE ROW LEVEL SECURITY" in sql
    assert "CREATE TABLE IF NOT EXISTS public.catalog_mutation_audit" in sql
    assert "ALTER TABLE public.catalog_mutation_audit ENABLE ROW LEVEL SECURITY" in sql
