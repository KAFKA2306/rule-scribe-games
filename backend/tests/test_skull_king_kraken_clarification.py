from pathlib import Path


MIGRATION = (
    Path(__file__).parents[1]
    / "app"
    / "db"
    / "migrations"
    / "125_add_skull_king_kraken_clarification.sql"
)


def sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_advanced_play_stays_separate_from_base_ruleset():
    body = sql()
    assert "COALESCE(rs.variant_label, '') = ''" in body
    assert "'variant_of', 'Advanced Play'" in body
    assert "base_rule_set_id = v_base_ruleset_id" in body
    assert '"scope":"advanced_play"' in body
    assert "false, 'current-web-rulebook-1764178570'" in body
    assert "'unknown', 'source_bound'" in body
    assert "is_active = false" in body
    assert "status = 'unknown'" in body


def test_current_kraken_ruling_is_supported_by_rulebook_and_official_faq():
    body = sql()
    current_claim = "skull-king:advanced:rule:kraken.next-lead.current"
    assert current_claim in body
    assert "'skull-king:rulebook:advanced-kraken'" in body
    assert "'skull-king:faq:kraken-next-lead'" in body
    assert body.count(current_claim) >= 3
    assert "'accepted'" in body


def test_conflicting_player_reference_is_preserved_without_guessing_print_run():
    body = sql()
    historical_claim = "skull-king:advanced:rule:kraken.next-lead.player-aid"
    assert "'player_reference_card'" in body
    assert '"print_run":"unresolved"' in body
    assert historical_claim in body
    assert body.count(historical_claim) >= 3
    assert "'rejected'" in body
    assert body.count("'contradicts'") >= 2


def test_migration_is_replay_safe_and_fails_when_canonical_base_is_missing():
    body = sql()
    assert "ON CONFLICT (source_id) DO UPDATE" in body
    assert "ON CONFLICT (locator_id) DO UPDATE" in body
    assert "ON CONFLICT (rule_set_id, rule_id) DO UPDATE" in body
    assert "ON CONFLICT (claim_id) DO UPDATE" in body
    assert "ON CONFLICT (binding_id) DO UPDATE" in body
    assert "RAISE EXCEPTION 'Active source-bound Skull King base RuleSet is required" in body
