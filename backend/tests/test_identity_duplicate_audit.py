from app.services.identity_coherence import audit_duplicate_title_candidates


def test_exact_duplicate_title_across_works_is_review_required() -> None:
    games = [
        {
            "id": "generic",
            "slug": "heart-of-crown",
            "work_id": "work-generic",
            "title": "Heart of Crown 2nd Edition",
            "title_ja": "ハートオブクラウン ～Heart of Crown～ 2nd Edition",
        },
        {
            "id": "edition",
            "slug": "heart-of-crown-2nd-edition",
            "work_id": "work-edition",
            "title": "Heart of Crown 2nd Edition",
            "title_ja": "ハートオブクラウン ～Heart of Crown～ 2nd Edition",
        },
    ]

    findings = audit_duplicate_title_candidates(games)

    assert len(findings) == 2
    assert {finding["reason"] for finding in findings} == {"exact_title_shared_across_multiple_works"}
    assert {tuple(finding["work_ids"]) for finding in findings} == {
        ("work-edition", "work-generic"),
    }
    assert all(finding["status"] == "review_required" for finding in findings)


def test_same_work_aliases_are_not_duplicate_candidates() -> None:
    games = [
        {
            "id": "base",
            "slug": "hack-clad",
            "work_id": "hackclad-work",
            "title": "HacKClaD",
            "title_ja": "ハッククラッド",
        },
        {
            "id": "legacy-view",
            "slug": "hackclad-shadow",
            "work_id": "hackclad-work",
            "title": "HacKClaD",
        },
    ]

    assert audit_duplicate_title_candidates(games) == []


def test_distinct_editions_are_candidates_not_auto_merge_decisions() -> None:
    games = [
        {
            "id": "old",
            "slug": "example-old",
            "work_id": "work-old",
            "title": "Example Game",
        },
        {
            "id": "new",
            "slug": "example-new",
            "work_id": "work-new",
            "title": "Example Game",
        },
    ]

    findings = audit_duplicate_title_candidates(games)

    assert findings == [
        {
            "normalized_title": "examplegame",
            "status": "review_required",
            "reason": "exact_title_shared_across_multiple_works",
            "work_ids": ["work-new", "work-old"],
            "candidates": [
                {
                    "game_id": "new",
                    "work_id": "work-new",
                    "slug": "example-new",
                    "field": "title",
                    "value": "Example Game",
                },
                {
                    "game_id": "old",
                    "work_id": "work-old",
                    "slug": "example-old",
                    "field": "title",
                    "value": "Example Game",
                },
            ],
        }
    ]
