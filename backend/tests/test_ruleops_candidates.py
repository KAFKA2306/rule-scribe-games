from app.scripts.ruleops_candidates import build_candidate, candidate_sort_key


def test_source_bound_game_is_not_a_candidate_for_migration():
    game = {
        "slug": "verified-game",
        "title": "Verified Game",
        "view_count": 7,
        "identity_status": "verified",
        "source_url": "https://publisher.example/rules",
        "source_trust": "official_publisher",
        "content_review_status": "human_reviewed",
    }

    candidate = build_candidate(
        game,
        has_source_bound=True,
        has_legacy_rules_content=False,
    )

    assert candidate.triage_state == "already_source_bound"
    assert candidate.blocker_reason is None


def test_unverified_identity_requires_review_before_source_work():
    game = {
        "slug": "unknown-edition",
        "title_ja": "版未確認",
        "view_count": 20,
        "amazon_url": "https://example.com/affiliate",
        "identity_status": "unverified",
        "source_url": "https://publisher.example/product",
        "source_trust": "official_publisher",
        "content_review_status": "review_required",
    }

    candidate = build_candidate(
        game,
        has_source_bound=False,
        has_legacy_rules_content=True,
    )

    assert candidate.has_affiliate_path is True
    assert candidate.triage_state == "needs_review"
    assert candidate.blocker_reason == "identity_not_verified"


def test_verified_primary_source_moves_to_source_triage_not_auto_verified():
    game = {
        "slug": "ready-for-research",
        "title": "Ready for Research",
        "view_count": 11,
        "identity_status": "verified",
        "source_url": "https://publisher.example/product",
        "source_trust": "official_publisher",
        "content_review_status": "review_required",
    }

    candidate = build_candidate(
        game,
        has_source_bound=False,
        has_legacy_rules_content=True,
    )

    assert candidate.triage_state == "source_triage"
    assert candidate.blocker_reason is None


def test_primary_source_is_required_for_source_triage():
    game = {
        "slug": "missing-source",
        "title": "Missing Source",
        "view_count": 9,
        "identity_status": "verified",
        "source_url": None,
        "source_trust": "unknown",
        "content_review_status": "review_required",
    }

    candidate = build_candidate(
        game,
        has_source_bound=False,
        has_legacy_rules_content=False,
    )

    assert candidate.triage_state == "needs_review"
    assert candidate.blocker_reason == "primary_source_not_bound"


def test_read_failure_is_reported_without_guessing_state():
    game = {
        "slug": "read-failed",
        "title": "Read Failed",
        "view_count": 12,
        "identity_status": "verified",
        "source_url": "https://publisher.example/product",
        "source_trust": "official_publisher",
    }

    candidate = build_candidate(
        game,
        has_source_bound=None,
        has_legacy_rules_content=None,
        read_error="TimeoutError: timed out",
    )

    assert candidate.triage_state == "blocked"
    assert candidate.blocker_reason == "production_read_failed"
    assert candidate.has_active_source_bound_ruleset is None


def test_priority_uses_direct_usage_then_commerce_then_search():
    common = {
        "identity_status": "verified",
        "source_url": "https://publisher.example/product",
        "source_trust": "official_publisher",
    }
    high_views = build_candidate(
        {**common, "slug": "a", "title": "A", "view_count": 20, "search_count": 1},
        has_source_bound=False,
        has_legacy_rules_content=True,
    )
    commerce = build_candidate(
        {
            **common,
            "slug": "b",
            "title": "B",
            "view_count": 10,
            "search_count": 2,
            "amazon_url": "https://example.com/affiliate",
        },
        has_source_bound=False,
        has_legacy_rules_content=True,
    )
    no_commerce = build_candidate(
        {**common, "slug": "c", "title": "C", "view_count": 10, "search_count": 99},
        has_source_bound=False,
        has_legacy_rules_content=True,
    )

    ranked = sorted([no_commerce, commerce, high_views], key=candidate_sort_key)

    assert [candidate.slug for candidate in ranked] == ["a", "b", "c"]
