from app.services.identity_coherence import audit_title_work_coherence


def test_title_alias_bound_to_multiple_works_requires_review() -> None:
    games = [
        {
            "id": "game-1",
            "slug": "first",
            "work_id": "work-1",
            "title": "Shared Title",
        },
        {
            "id": "game-2",
            "slug": "second",
            "work_id": "work-2",
            "title": "Shared Title",
        },
    ]
    aliases = [
        {"game_id": "game-1", "title": "Shared Title"},
        {"game_id": "game-2", "title": "Shared Title"},
    ]

    findings = audit_title_work_coherence(games, aliases)

    assert findings == [
        {
            "game_id": "game-1",
            "slug": "first",
            "work_id": "work-1",
            "field": "title",
            "value": "Shared Title",
            "status": "review_required",
            "reason": "title_alias_bound_to_multiple_works",
            "bound_work_ids": ["work-1", "work-2"],
        },
        {
            "game_id": "game-2",
            "slug": "second",
            "work_id": "work-2",
            "field": "title",
            "value": "Shared Title",
            "status": "review_required",
            "reason": "title_alias_bound_to_multiple_works",
            "bound_work_ids": ["work-1", "work-2"],
        },
    ]
