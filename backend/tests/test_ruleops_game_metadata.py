from app.scripts.ruleops_generate_migration import generate_migration
from app.scripts.ruleops_manifest import validate_manifest


def game_with_metadata():
    revision = "publisher-2026-example"
    return {
        "slug": "example-game",
        "identity": {
            "title": "Example Game",
            "edition": "Base Game 2026",
            "language": "ja",
            "platform": "physical",
            "revision": revision,
        },
        "scope": {
            "included_product": "Base Game 2026",
            "excluded_products": ["Expansion"],
        },
        "review_status": "reviewed",
        "remove_legacy_authority": True,
        "sources": [
            {
                "source_id": "publisher:example:rulebook",
                "url": "https://publisher.example/example/rules.pdf",
                "source_type": "publisher_rulebook",
                "revision_label": "2026 rules",
                "review_status": "reviewed",
                "applies_to_revision": revision,
                "applies_to_platform": "physical",
            },
            {
                "source_id": "publisher:example:product",
                "url": "https://publisher.example/example",
                "source_type": "publisher_product_page",
                "revision_label": "2026 product page",
                "review_status": "reviewed",
                "applies_to_revision": revision,
                "applies_to_platform": "physical",
            },
        ],
        "rules": [
            {
                "rule_id": "turn.draw",
                "node_type": "turn",
                "claim": "手番ではカードを1枚引く。",
                "source_id": "publisher:example:rulebook",
                "evidence_locator": "p.2 Turn",
                "review_status": "reviewed",
            }
        ],
        "metadata": [
            {
                "field": "min_players",
                "value": 2,
                "display": "2～10人",
                "unit": "players",
                "source_id": "publisher:example:product",
                "evidence_locator": "商品概要 / プレイ人数",
                "review_status": "reviewed",
            },
            {
                "field": "max_players",
                "value": 10,
                "display": "2～10人",
                "unit": "players",
                "source_id": "publisher:example:product",
                "evidence_locator": "商品概要 / プレイ人数",
                "review_status": "reviewed",
            },
            {
                "field": "play_time",
                "value": 30,
                "display": "約30分",
                "unit": "minutes",
                "approximate": True,
                "source_id": "publisher:example:product",
                "evidence_locator": "商品概要 / プレイ時間",
                "review_status": "reviewed",
            },
            {
                "field": "published_year",
                "value": 2026,
                "display": "2026年",
                "unit": "year",
                "source_id": "publisher:example:product",
                "evidence_locator": "商品概要 / 発売日",
                "review_status": "reviewed",
            },
        ],
    }


def manifest(game):
    return {"schema_version": "1.0", "batch_id": "metadata-pilot", "games": [game]}


def test_reviewed_metadata_is_ready_and_product_page_can_support_it():
    report = validate_manifest(manifest(game_with_metadata()))

    assert report["status"] == "ready"
    assert report["ready_games"] == 1


def test_metadata_validation_blocks_range_unit_source_and_review_failures():
    game = game_with_metadata()
    game["metadata"][0]["value"] = 11
    game["metadata"][1]["value"] = 10
    game["metadata"][2]["unit"] = "players"
    game["metadata"][2]["source_id"] = "publisher:missing"
    game["metadata"][3]["review_status"] = "needs_review"

    report = validate_manifest(manifest(game))
    codes = {error["code"] for error in report["games"][0]["errors"]}

    assert "invalid_player_range" in codes
    assert "metadata_unit_mismatch" in codes
    assert "missing_metadata_source" in codes
    assert "metadata_not_reviewed" in codes


def test_duplicate_metadata_field_is_blocked_before_generation():
    game = game_with_metadata()
    game["metadata"].append(dict(game["metadata"][0]))

    report = validate_manifest(manifest(game))

    assert any(error["code"] == "duplicate_metadata_field" for error in report["games"][0]["errors"])


def test_generator_updates_canonical_metadata_and_writes_matching_evidence():
    sql, report = generate_migration(manifest(game_with_metadata()), "076")

    assert report["status"] == "generated"
    assert "min_players=2" in sql
    assert "max_players=10" in sql
    assert "play_time=30" in sql
    assert "published_year=2026" in sql
    assert "example-game:metadata:min_players" in sql
    assert "example-game:binding:metadata:max_players" in sql
    assert "example-game:locator:metadata:play_time" in sql
    assert "'game_metadata_value'" in sql
    assert "'game_metadata'" in sql
    assert '"approximate":true' in sql
    assert "canonical max_players must equal reviewed metadata value 10" in sql
    assert "metadata evidence published_year must exist exactly once" in sql


def test_manifest_without_metadata_keeps_existing_ruleops_behavior():
    game = game_with_metadata()
    del game["metadata"]

    sql, report = generate_migration(manifest(game), "076")

    assert report["status"] == "generated"
    assert ":metadata:" not in sql
    assert "target_type='game_metadata'" not in sql
