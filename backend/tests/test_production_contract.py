import json

import pytest

import app.scripts.verify_production_contract as production_contract
from app.scripts.verify_production_contract import (
    build_indexability_report,
    fetch_public_games,
    indexability_reasons,
    validate_anonymous_catalog_patch_status,
    validate_mechanical_dna_payload,
    validate_public_cache_observation,
    validate_source_bound_glossary_payload,
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


def test_validate_source_bound_glossary_payload_accepts_canonical_rule_reference():
    payload = {
        "status": "available",
        "entries": [
            {
                "label": "ビッド",
                "rule_references": [
                    {
                        "verification_status": "source_bound",
                        "rule_set_id": "current-rule-set",
                        "source_url": "https://example.com/official-rules",
                    }
                ],
            }
        ],
    }

    assert validate_source_bound_glossary_payload(payload) == 1


def test_validate_source_bound_glossary_payload_fails_when_rule_links_are_missing():
    payload = {
        "status": "available",
        "entries": [{"label": "ビッド", "rule_references": []}],
    }

    with pytest.raises(ValueError, match="no source-bound rule references"):
        validate_source_bound_glossary_payload(payload)


@pytest.mark.parametrize("missing_field", ["rule_set_id", "source_url"])
def test_validate_source_bound_glossary_payload_requires_current_ruleset_and_source(missing_field):
    reference = {
        "verification_status": "source_bound",
        "rule_set_id": "current-rule-set",
        "source_url": "https://example.com/official-rules",
    }
    reference[missing_field] = ""
    payload = {
        "status": "available",
        "entries": [{"label": "ビッド", "rule_references": [reference]}],
    }

    with pytest.raises(ValueError, match=missing_field):
        validate_source_bound_glossary_payload(payload)


def test_validate_public_cache_observation_accepts_second_request_hit():
    validate_public_cache_observation(200, 200, b'{"slug":"skull-king"}', b'{"slug":"skull-king"}', "HIT")


@pytest.mark.parametrize("cache_status", [None, "MISS", "BYPASS", "STALE"])
def test_validate_public_cache_observation_requires_actual_second_request_hit(cache_status):
    with pytest.raises(ValueError, match="did not hit Vercel CDN"):
        validate_public_cache_observation(200, 200, b"same", b"same", cache_status)


def test_validate_public_cache_observation_rejects_changed_body():
    with pytest.raises(ValueError, match="different response bodies"):
        validate_public_cache_observation(200, 200, b"first", b"second", "HIT")


@pytest.mark.parametrize("status_code", [401, 403])
def test_anonymous_catalog_patch_accepts_auth_rejection(status_code):
    validate_anonymous_catalog_patch_status(status_code)


@pytest.mark.parametrize("status_code", [200, 204, 400, 404, 422, 500])
def test_anonymous_catalog_patch_rejects_other_statuses(status_code):
    with pytest.raises(ValueError, match="anonymous catalog PATCH must fail"):
        validate_anonymous_catalog_patch_status(status_code)


def test_fetch_public_games_paginates_within_api_limit(monkeypatch):
    requested_paths = []

    def fake_request(base_url, path, timeout_seconds, accept):
        requested_paths.append(path)
        offset = int(path.split("offset=")[1])
        total = 185
        size = min(100, total - offset)
        body = json.dumps({"total": total, "games": [{"slug": f"game-{i}"} for i in range(offset, offset + size)]}).encode()
        return 200, body

    monkeypatch.setattr(production_contract, "_request", fake_request)

    games = fetch_public_games("https://example.test")

    assert len(games) == 185
    assert requested_paths == [
        "/api/games?limit=100&offset=0",
        "/api/games?limit=100&offset=100",
    ]


def test_fetch_public_games_fails_if_pagination_ends_early(monkeypatch):
    def fake_request(base_url, path, timeout_seconds, accept):
        offset = int(path.split("offset=")[1])
        if offset == 0:
            return 200, json.dumps({"total": 185, "games": [{"slug": f"game-{i}"} for i in range(100)]}).encode()
        return 200, json.dumps({"total": 185, "games": []}).encode()

    monkeypatch.setattr(production_contract, "_request", fake_request)

    with pytest.raises(ValueError, match="ended before total rows"):
        fetch_public_games("https://example.test")


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
