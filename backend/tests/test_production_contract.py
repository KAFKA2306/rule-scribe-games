import pytest

from app.scripts.verify_production_contract import (
    build_indexability_report,
    indexability_reasons,
    validate_anonymous_catalog_patch_status,
    validate_mechanical_dna_payload,
)


def test_validate_mechanical_dna_payload_accepts_canonical_contract():
    payload = {
        "schema_version": "1.0",
        "algorithm_version": "mechanical-dna-concept-v1",
        "status": "available",
        "game_id": "game-id",
        "slug": "skull-king",
        "connections": [],
    }

    assert validate_mechanical_dna_payload(payload) == 0


def test_validate_mechanical_dna_payload_allows_future_connections():
    payload = {
        "schema_version": "1.0",
        "algorithm_version": "mechanical-dna-concept-v1",
        "status": "available",
        "slug": "skull-king",
        "connections": [{"slug": "another-game"}],
    }

    assert validate_mechanical_dna_payload(payload) == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("algorithm_version", "legacy-label-match"),
        ("status", "not_available"),
        ("slug", "other-game"),
        ("connections", None),
    ],
)
def test_validate_mechanical_dna_payload_fails_closed(field, value):
    payload = {
        "schema_version": "1.0",
        "algorithm_version": "mechanical-dna-concept-v1",
        "status": "available",
        "slug": "skull-king",
        "connections": [],
    }
    payload[field] = value

    with pytest.raises(ValueError):
        validate_mechanical_dna_payload(payload)


@pytest.mark.parametrize("status_code", [401, 403])
def test_anonymous_catalog_patch_accepts_auth_rejection(status_code):
    validate_anonymous_catalog_patch_status(status_code)


@pytest.mark.parametrize("status_code", [200, 204, 400, 404, 422, 500])
def test_anonymous_catalog_patch_rejects_other_statuses(status_code):
    with pytest.raises(ValueError, match="anonymous catalog PATCH must fail"):
        validate_anonymous_catalog_patch_status(status_code)


def test_indexability_reasons_keep_unreviewed_games_out_of_search():
    assert indexability_reasons(
        {"identity_status": "verified", "content_review_status": "review_required"}
    ) == ("content_not_human_reviewed",)
    assert indexability_reasons(
        {"identity_status": "unverified", "content_review_status": "human_reviewed"}
    ) == ("identity_not_verified",)


def test_build_indexability_report_matches_sitemap_and_counts_reasons():
    base_url = "https://example.test"
    games = [
        {
            "slug": "reviewed",
            "identity_status": "verified",
            "content_review_status": "human_reviewed",
        },
        {
            "slug": "needs-review",
            "identity_status": "verified",
            "content_review_status": "review_required",
        },
        {
            "slug": "unverified",
            "identity_status": "unverified",
            "content_review_status": "unknown",
        },
    ]
    sitemap_urls = {
        f"{base_url}/",
        f"{base_url}/data",
        f"{base_url}/games/reviewed",
    }

    report = build_indexability_report(games, sitemap_urls, base_url)

    assert report == {
        "public_games": 3,
        "indexable": 1,
        "non_indexable": 2,
        "reason_counts": {
            "content_not_human_reviewed": 2,
            "identity_not_verified": 1,
        },
        "sitemap_game_urls": 1,
        "missing_from_sitemap": [],
        "unexpected_in_sitemap": [],
    }


def test_build_indexability_report_fails_on_sitemap_drift():
    games = [
        {
            "slug": "reviewed",
            "identity_status": "verified",
            "content_review_status": "human_reviewed",
        }
    ]

    with pytest.raises(ValueError, match="sitemap does not match"):
        build_indexability_report(games, set(), "https://example.test")
