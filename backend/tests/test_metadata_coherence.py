from app.services.metadata_coherence import audit_metadata_source_work_coherence


def _game(**overrides):
    game = {
        "id": "game-1",
        "slug": "sample",
        "work_id": "work-1",
        "source_url": "https://publisher.example/sample",
        "min_players": 2,
        "max_players": 4,
        "play_time": 30,
        "min_age": 8,
        "published_year": 2024,
    }
    game.update(overrides)
    return game


def test_metadata_source_bound_only_to_current_work_is_coherent() -> None:
    games = [_game()]
    bindings = {"https://publisher.example/sample": {"work-1"}}

    assert audit_metadata_source_work_coherence(games, bindings) == []


def test_metadata_without_source_requires_review() -> None:
    findings = audit_metadata_source_work_coherence([_game(source_url=None)], {})

    assert findings == [
        {
            "game_id": "game-1",
            "slug": "sample",
            "work_id": "work-1",
            "fields": ["min_players", "max_players", "play_time", "min_age", "published_year"],
            "source_url": None,
            "status": "review_required",
            "reason": "metadata_source_missing",
            "bound_work_ids": [],
        }
    ]


def test_metadata_with_unbound_source_requires_review() -> None:
    findings = audit_metadata_source_work_coherence([_game()], {})

    assert findings[0]["status"] == "review_required"
    assert findings[0]["reason"] == "metadata_source_unbound"
    assert findings[0]["bound_work_ids"] == []


def test_metadata_source_bound_to_different_work_is_conflict() -> None:
    bindings = {"https://publisher.example/sample": {"work-2"}}

    findings = audit_metadata_source_work_coherence([_game()], bindings)

    assert findings[0]["status"] == "identity_conflict"
    assert findings[0]["reason"] == "metadata_source_bound_to_different_work"
    assert findings[0]["bound_work_ids"] == ["work-2"]


def test_metadata_source_bound_to_multiple_works_requires_review() -> None:
    bindings = {"https://publisher.example/sample": {"work-1", "work-2"}}

    findings = audit_metadata_source_work_coherence([_game()], bindings)

    assert findings[0]["status"] == "review_required"
    assert findings[0]["reason"] == "metadata_source_bound_to_multiple_works"
    assert findings[0]["bound_work_ids"] == ["work-1", "work-2"]


def test_only_populated_metadata_fields_are_reported() -> None:
    game = _game(max_players=None, play_time=None, min_age=None, published_year=None)

    findings = audit_metadata_source_work_coherence([game], {})

    assert findings[0]["fields"] == ["min_players"]


def test_game_without_metadata_is_not_reported() -> None:
    game = _game(
        min_players=None,
        max_players=None,
        play_time=None,
        min_age=None,
        published_year=None,
        source_url=None,
    )

    assert audit_metadata_source_work_coherence([game], {}) == []
