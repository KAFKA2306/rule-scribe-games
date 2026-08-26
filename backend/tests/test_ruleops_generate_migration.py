import pytest

from app.scripts.ruleops_generate_migration import generate_migration, safe_identifier
from app.scripts.ruleops_manifest import validate_manifest


def valid_game(slug: str, claim: str = "手番ではカードを1枚引く。"):
    revision = f"publisher-2026-{slug}"
    return {
        "slug": slug,
        "identity": {
            "title": f"Game {slug}",
            "edition": "Base Game 2026",
            "language": "ja",
            "platform": "physical",
            "revision": revision,
        },
        "scope": {
            "included_product": "Base Game 2026",
            "excluded_products": ["Expansion", "Digital Edition"],
        },
        "review_status": "reviewed",
        "remove_legacy_authority": True,
        "sources": [
            {
                "source_id": f"publisher:{slug}:rulebook",
                "url": f"https://publisher.example/{slug}/rules.pdf",
                "source_type": "publisher_rulebook",
                "revision_label": "2026 rules",
                "review_status": "reviewed",
                "applies_to_revision": revision,
                "applies_to_platform": "physical",
            }
        ],
        "rules": [
            {
                "rule_id": "turn.draw",
                "node_type": "turn",
                "claim": claim,
                "source_id": f"publisher:{slug}:rulebook",
                "evidence_locator": "p.2 Turn",
                "review_status": "reviewed",
            }
        ],
    }


def manifest(*games):
    return {"schema_version": "1.0", "batch_id": "pilot batch/001", "games": list(games)}


def test_generator_emits_one_transaction_for_multiple_ready_games():
    payload = manifest(valid_game("alpha"), valid_game("beta", "手番ではカードを1枚出す。"))

    sql, report = generate_migration(payload, "071")

    assert report["status"] == "generated"
    assert report["generated_games"] == ["alpha", "beta"]
    assert sql.startswith("BEGIN;")
    assert sql.rstrip().endswith("COMMIT;")
    assert "RuleOps game: alpha" in sql
    assert "RuleOps game: beta" in sql
    assert "INSERT INTO public.evidence_sources" in sql
    assert "INSERT INTO public.rule_sets" in sql
    assert "INSERT INTO public.rule_nodes" in sql
    assert "INSERT INTO public.claims" in sql
    assert "INSERT INTO public.evidence_bindings" in sql
    assert "RuleOps alpha RuleNode count must be 1" in sql
    assert "RuleOps beta EvidenceBinding count must be 1" in sql


def test_blocked_game_is_reported_and_not_rendered_into_sql():
    good = valid_game("good")
    bad = valid_game("bad")
    bad["identity"]["revision"] = "wrong-revision"
    payload = manifest(good, bad)

    validation = validate_manifest(payload)
    assert validation["ready_games"] == 1
    assert validation["blocked_games"] == 1

    sql, report = generate_migration(payload, "071")

    assert report["status"] == "generated_with_blocks"
    assert report["generated_games"] == ["good"]
    assert report["blocked_games"][0]["slug"] == "bad"
    assert "RuleOps game: good" in sql
    assert "RuleOps game: bad" not in sql


def test_generator_refuses_manifest_without_ready_game():
    bad = valid_game("bad")
    bad["rules"][0]["node_type"] = "penalty"

    with pytest.raises(ValueError, match="no ready games"):
        generate_migration(manifest(bad), "071")


def test_generated_sql_preserves_edition_boundary_and_removes_legacy_authority():
    game = valid_game("gamma")
    game["identity"]["edition"] = "Second Edition"
    game["scope"]["excluded_products"] = ["First Edition", "Digital Edition"]

    sql, _ = generate_migration(manifest(game), "071")

    assert "edition_label='Second Edition'" in sql
    assert "rules_content=NULL" in sql
    assert "structured_data='{}'::jsonb" in sql
    assert "revision_label,'publisher-2026-gamma'" in sql


def test_sql_literals_escape_quotes_and_batch_name_is_filename_safe():
    game = valid_game("quote-game", "カードを'1枚'引く。")

    sql, _ = generate_migration(manifest(game), "071")

    assert "カードを''1枚''引く。" in sql
    assert safe_identifier("pilot batch/001") == "pilot_batch_001"
