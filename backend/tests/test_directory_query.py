import pytest

from app.services import directory_query


def _game(
    game_id: str,
    *,
    title: str,
    minimum: int,
    maximum: int,
    play_time: int,
    year: int,
    created_at: str,
    tier: str | None = None,
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
        "published_year": year,
        "created_at": created_at,
        "strategy_tier": tier,
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
