from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import GameDetail, GameUpdate

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase" / "migrations" / "20260814071000_trust_semantics_139.sql"


def test_game_detail_defaults_are_conservative():
    game = GameDetail(id="1", title="Example")
    assert game.identity_status == "unverified"
    assert game.source_trust_status == "unknown"
    assert game.content_review_status == "ai_draft"
    assert game.is_official is False


def test_invalid_source_trust_is_rejected():
    with pytest.raises(ValidationError):
        GameDetail(id="1", title="Example", source_trust_status="official")


def test_manual_update_does_not_expose_identity_or_legacy_official_flags():
    fields = GameUpdate.model_fields
    assert "identity_status" not in fields
    assert "is_official" not in fields
    assert "source_trust_status" in fields
    assert "content_review_status" in fields


def test_migration_backfills_only_from_explicit_source_documents():
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "structured_data->'source_documents'" in sql
    assert "publisher_official" in sql
    assert "platform_official_rules" in sql
    assert "official_url is not null" not in sql.lower()
    assert "bga_url is not null" not in sql.lower()


def test_migration_blocks_unverified_legacy_official_state():
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "set is_official = false" in sql.lower()
    assert "not coalesce(is_official, false) or identity_status = 'verified'" in sql.lower()
