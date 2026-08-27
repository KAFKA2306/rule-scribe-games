import pytest

from app.services import directory_query


def _game(
    game_id: str,
    *,
    title: str,
    minimum: int,
    maximum: int,
    play_time: int | None,
    year: int,
    created_at: str,
    play_time_min_minutes: int | None = None,
    play_time_max_minutes: int | None = None,
    tier: str | None = None,
    identity_status: str = "verified",
    content_review_status: str = "human_reviewed",
):
    return {
        "id": game_id,
        "title": title,
        "title_ja": title,
        "title_en": None,
        "summary": f"{title} summary",
        "description": None,
        "min_players": minimum,
        "max_players": maximum,
        "play_time": play_time,
        "play_time_min_minutes": play_time_min_minutes,
        "play_time_max_minutes": play_time_max_minutes,
        "published_year": year,
        "created_at": created_at,
        "strategy_tier": tier,
        "identity_status": identity_status,
        "content_review_status": content_review_status,
    }


def test_local_directory_filters_before_pagination(monkeypatch):
    rows = [
        _game("a", title="Alpha", minimum=2, maximum=4, play_time=25, year=2024, created_at="2024-01-01", tier="A"),
        _game("b", title="Beta", minimum=5, maximum=6, play_time=45, year=2023, created_at="2025-01-01", tier="B"),
        _game("c", title="Alpha Plus", minimum=3, maximum=5, play_time=80, year=2025, created_at="2026-01-01", tier="A"),
    ]
    monkeypatch.setattr(directory_query.local_db, "list_recent", lambda limit, offset: {"data": rows, "total": len(rows)})

    result = directory_query._query_local(
        q="alpha",
        players="3",
        time_filter="60-120",
        tier="A",
        sort="recent",
        limit=48,
        offset=0,
    )

    assert result["total"] == 1
    assert [game["id"] for game in result["data"]] == ["c"]


def test_time_filter_uses_range_overlap_without_rounding():
    skull_king = _game(
        "skull-king",
        title="Skull King",
        minimum=2,
        maximum=8,
        play_time=None,
        play_time_min_minutes=30,
        play_time_max_minutes=45,
        year=2013,
        created_at="2020-01-01",
    )

    assert directory_query._matches_time(skull_king, "30-")
    assert directory_query._matches_time(skull_king, "30-60")
    assert not directory_query._matches_time(skull_king, "60-120")
    assert not directory_query._matches_time(skull_king, "120+")


def test_time_filter_boundary_overlap_is_inclusive():
    exactly_60 = _game(
        "sixty",
        title="Sixty",
        minimum=2,
        maximum=4,
        play_time=None,
        play_time_min_minutes=60,
        play_time_max_minutes=60,
        year=2026,
        created_at="2026-01-01",
    )

    assert directory_query._matches_time(exactly_60, "30-60")
    assert directory_query._matches_time(exactly_60, "60-120")


def test_time_filter_rejects_unknown_or_malformed_ranges():
    unknown = _game("unknown", title="Unknown", minimum=2, maximum=4, play_time=None, year=2026, created_at="2026-01-01")
    malformed = _game(
        "bad",
        title="Bad",
        minimum=2,
        maximum=4,
        play_time=None,
        play_time_min_minutes=60,
        play_time_max_minutes=30,
        year=2026,
        created_at="2026-01-01",
    )

    assert not directory_query._matches_time(unknown, "30-60")
    assert not directory_query._matches_time(malformed, "30-60")


def test_local_directory_paginates_sorted_results(monkeypatch):
    rows = [
        _game("old", title="Old", minimum=2, maximum=4, play_time=30, year=2020, created_at="2020-01-01"),
        _game("new", title="New", minimum=2, maximum=4, play_time=30, year=2026, created_at="2026-01-01"),
        _game("middle", title="Middle", minimum=2, maximum=4, play_time=30, year=2023, created_at="2023-01-01"),
    ]
    monkeypatch.setattr(directory_query.local_db, "list_recent", lambda limit, offset: {"data": rows, "total": len(rows)})

    result = directory_query._query_local(
        q=None,
        players=None,
        time_filter=None,
        tier=None,
        sort="recent",
        limit=1,
        offset=1,
    )

    assert result["total"] == 3
    assert [game["id"] for game in result["data"]] == ["middle"]


def test_five_plus_filter_matches_games_that_support_at_least_five(monkeypatch):
    rows = [
        _game("four", title="Four", minimum=2, maximum=4, play_time=30, year=2024, created_at="2024-01-01"),
        _game("five", title="Five", minimum=2, maximum=5, play_time=30, year=2024, created_at="2024-01-02"),
    ]
    monkeypatch.setattr(directory_query.local_db, "list_recent", lambda limit, offset: {"data": rows, "total": len(rows)})

    result = directory_query._query_local(
        q=None,
        players="5+",
        time_filter=None,
        tier=None,
        sort="recent",
        limit=48,
        offset=0,
    )

    assert result["total"] == 1
    assert result["data"][0]["id"] == "five"


def test_ranked_search_keeps_canonical_relevance_for_default_sort():
    rows = [
        _game("exact", title="Skull King", minimum=2, maximum=8, play_time=45, year=2013, created_at="2020-01-01"),
        _game("summary", title="Pirate Tricks", minimum=2, maximum=4, play_time=30, year=2026, created_at="2026-01-01"),
    ]

    result = directory_query._query_ranked_search_results(
        rows,
        players=None,
        time_filter=None,
        tier=None,
        sort="recent",
        limit=48,
        offset=0,
    )

    assert [game["id"] for game in result["data"]] == ["exact", "summary"]


def test_directory_hides_unverified_and_unreviewed_prose(monkeypatch):
    rows = [
        _game(
            "unverified",
            title="Unverified",
            minimum=2,
            maximum=4,
            play_time=30,
            year=2026,
            created_at="2026-01-03",
            identity_status="unverified",
            content_review_status="unknown",
        ),
        _game(
            "needs-review",
            title="Needs Review",
            minimum=2,
            maximum=4,
            play_time=30,
            year=2026,
            created_at="2026-01-02",
            content_review_status="review_required",
        ),
        _game(
            "reviewed",
            title="Reviewed",
            minimum=2,
            maximum=4,
            play_time=30,
            year=2026,
            created_at="2026-01-01",
        ),
    ]
    monkeypatch.setattr(directory_query.local_db, "list_recent", lambda limit, offset: {"data": rows, "total": len(rows)})

    result = directory_query._query_local(
        q=None,
        players=None,
        time_filter=None,
        tier=None,
        sort="recent",
        limit=48,
        offset=0,
    )

    projected = {game["id"]: game for game in result["data"]}
    assert projected["unverified"]["summary"] == "概要は確認中です。"
    assert projected["needs-review"]["summary"] == "概要は確認中です。"
    assert projected["reviewed"]["summary"] == "Reviewed summary"


@pytest.mark.asyncio
async def test_directory_query_reuses_canonical_search(monkeypatch):
    ranked = [
        _game("alias-hit", title="6 nimmt!", minimum=2, maximum=10, play_time=45, year=1994, created_at="2020-01-01"),
        _game("other", title="11 nimmt!", minimum=2, maximum=7, play_time=30, year=2010, created_at="2026-01-01"),
    ]
    calls = []

    async def fake_search(query):
        calls.append(query)
        return ranked

    monkeypatch.setattr(directory_query.supabase, "search", fake_search)

    result = await directory_query.list_directory_games(q="6 Nimmt", limit=1)

    assert calls == ["6 Nimmt"]
    assert result["total"] == 2
    assert [game["id"] for game in result["data"]] == ["alias-hit"]