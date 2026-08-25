from app.scripts.ruleops_manifest import validate_manifest


def valid_game(slug: str = "example-game"):
    revision = "publisher-2026-base"
    return {
        "slug": slug,
        "identity": {
            "title": "Example Game",
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
                "source_id": "publisher:example:rulebook",
                "url": "https://publisher.example/rules.pdf",
                "source_type": "publisher_rulebook",
                "revision_label": "2026 rules",
                "review_status": "reviewed",
                "applies_to_revision": revision,
                "applies_to_platform": "physical",
            }
        ],
        "rules": [
            {
                "rule_id": "setup.base",
                "node_type": "setup",
                "claim": "各プレイヤーに初期手札を配る。",
                "source_id": "publisher:example:rulebook",
                "evidence_locator": "p.2 Setup",
                "review_status": "reviewed",
            }
        ],
    }


def test_valid_reviewed_manifest_is_ready():
    report = validate_manifest(
        {"schema_version": "1.0", "batch_id": "pilot-001", "games": [valid_game()]}
    )

    assert report["status"] == "ready"
    assert report["ready_games"] == 1
    assert report["blocked_games"] == 0


def test_invalid_game_does_not_hide_ready_sibling():
    bad = valid_game("bad-game")
    bad["identity"]["revision"] = "other-revision"

    report = validate_manifest(
        {
            "schema_version": "1.0",
            "batch_id": "pilot-002",
            "games": [valid_game("good-game"), bad],
        }
    )

    assert report["status"] == "blocked"
    assert report["ready_games"] == 1
    assert report["blocked_games"] == 1
    bad_result = next(game for game in report["games"] if game["slug"] == "bad-game")
    assert any(error["code"] == "revision_mismatch" for error in bad_result["errors"])


def test_identity_only_source_cannot_support_rule_claim():
    game = valid_game()
    game["sources"][0]["source_type"] = "publisher_product_page"

    report = validate_manifest(
        {"schema_version": "1.0", "batch_id": "pilot-003", "games": [game]}
    )

    errors = report["games"][0]["errors"]
    assert any(error["code"] == "non_rule_source" for error in errors)


def test_invalid_node_type_is_rejected_before_sql_generation():
    game = valid_game()
    game["rules"][0]["node_type"] = "penalty"

    report = validate_manifest(
        {"schema_version": "1.0", "batch_id": "pilot-004", "games": [game]}
    )

    errors = report["games"][0]["errors"]
    assert any(error["code"] == "invalid_node_type" for error in errors)


def test_missing_evidence_and_duplicate_binding_are_rejected():
    game = valid_game()
    game["rules"].append(
        {
            "rule_id": "setup.second",
            "node_type": "setup",
            "claim": "別の準備を行う。",
            "source_id": "publisher:example:rulebook",
            "evidence_locator": "p.2 Setup",
            "review_status": "reviewed",
        }
    )
    game["rules"][0]["evidence_locator"] = ""

    report = validate_manifest(
        {"schema_version": "1.0", "batch_id": "pilot-005", "games": [game]}
    )

    errors = report["games"][0]["errors"]
    assert any(error["code"] == "missing_evidence_locator" for error in errors)


def test_duplicate_rule_claim_and_source_are_rejected():
    game = valid_game()
    duplicate = dict(game["rules"][0])
    game["rules"].append(duplicate)
    game["sources"].append(dict(game["sources"][0]))

    report = validate_manifest(
        {"schema_version": "1.0", "batch_id": "pilot-006", "games": [game]}
    )

    codes = {error["code"] for error in report["games"][0]["errors"]}
    assert "duplicate_source" in codes
    assert "duplicate_rule" in codes
    assert "duplicate_claim" in codes
    assert "duplicate_binding" in codes


def test_unreviewed_game_source_or_rule_is_blocked():
    game = valid_game()
    game["review_status"] = "needs_review"
    game["sources"][0]["review_status"] = "needs_review"
    game["rules"][0]["review_status"] = "needs_review"

    report = validate_manifest(
        {"schema_version": "1.0", "batch_id": "pilot-007", "games": [game]}
    )

    codes = {error["code"] for error in report["games"][0]["errors"]}
    assert {"game_not_reviewed", "source_not_reviewed", "rule_not_reviewed"} <= codes


def test_unsupported_schema_version_blocks_batch():
    report = validate_manifest(
        {"schema_version": "2.0", "batch_id": "pilot-008", "games": [valid_game()]}
    )

    assert report["status"] == "blocked"
    assert report["batch_errors"][0]["code"] == "unsupported_schema_version"
