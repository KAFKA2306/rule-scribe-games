from app.services.identity_coherence import audit_title_work_coherence


def test_same_work_verified_aliases_are_coherent() -> None:
    games = [
        {
            "id": "game-1",
            "slug": "sample",
            "work_id": "work-1",
            "title": "Sample Game",
            "title_ja": "サンプルゲーム",
        }
    ]
    aliases = [
        {"game_id": "game-1", "title": "Sample Game"},
        {"game_id": "game-1", "title": "サンプルゲーム"},
    ]

    assert audit_title_work_coherence(games, aliases) == []


def test_title_bound_to_another_work_is_identity_conflict() -> None:
    games = [
        {
            "id": "game-1",
            "slug": "first",
            "work_id": "work-1",
            "title": "First Game",
            "title_ja": "別のゲーム",
        },
        {
            "id": "game-2",
            "slug": "second",
            "work_id": "work-2",
            "title": "別のゲーム",
        },
    ]
    aliases = [
        {"game_id": "game-1", "title": "First Game"},
        {"game_id": "game-2", "title": "別のゲーム"},
    ]

    findings = audit_title_work_coherence(games, aliases)

    assert findings == [
        {
            "game_id": "game-1",
            "slug": "first",
            "work_id": "work-1",
            "field": "title_ja",
            "value": "別のゲーム",
            "status": "identity_conflict",
            "reason": "title_bound_to_different_work",
            "bound_work_ids": ["work-2"],
        }
    ]


def test_unknown_title_requires_review_instead_of_guessing() -> None:
    games = [
        {
            "id": "game-1",
            "slug": "sample",
            "work_id": "work-1",
            "title": "Sample Game",
            "title_en": "Unreviewed Alias",
        }
    ]
    aliases = [{"game_id": "game-1", "title": "Sample Game"}]

    findings = audit_title_work_coherence(games, aliases)

    assert findings[0]["field"] == "title_en"
    assert findings[0]["status"] == "review_required"
    assert findings[0]["reason"] == "title_has_no_verified_alias_binding"
    assert findings[0]["bound_work_ids"] == []


def test_nfkc_and_casefold_match_verified_alias() -> None:
    games = [
        {
            "id": "game-1",
            "slug": "sample",
            "work_id": "work-1",
            "title": "ＳＡＭＰＬＥ　ＧＡＭＥ",
        }
    ]
    aliases = [{"game_id": "game-1", "title": "sample game"}]

    assert audit_title_work_coherence(games, aliases) == []
