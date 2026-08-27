import unicodedata
from typing import Any, Literal

import anyio

from app.core import local_db, supabase
from app.services.metadata_evidence_projection import project_metadata_evidence
from app.services.player_summary import project_directory_summary
from app.services.search_visibility import EXCLUDED_GAME_SLUGS, should_hide_game_from_search

DirectorySort = Literal["recent", "title", "year", "play_time"]
DirectoryTime = Literal["30-", "30-60", "60-120", "120+"]


def _normalize(value: str | None) -> str:
    return unicodedata.normalize("NFKC", value or "").casefold().strip()


def _matches_query(game: dict[str, Any], query: str) -> bool:
    needle = _normalize(query)
    if not needle:
        return True
    return any(
        needle in _normalize(str(game.get(field) or ""))
        for field in ("title", "title_ja", "title_en", "summary", "description")
    )


def _matches_players(game: dict[str, Any], players: str | None) -> bool:
    if not players:
        return True
    minimum = game.get("min_players")
    maximum = game.get("max_players")
    if not isinstance(minimum, int) or not isinstance(maximum, int) or minimum <= 0 or maximum <= 0:
        return False
    if players == "5+":
        return maximum >= 5
    player_count = int(players)
    return minimum <= player_count <= maximum


def _duration_range(game: dict[str, Any]) -> tuple[int, int] | None:
    minimum = game.get("play_time_min_minutes")
    maximum = game.get("play_time_max_minutes")
    if isinstance(minimum, int) and isinstance(maximum, int) and minimum > 0 and maximum >= minimum:
        return minimum, maximum
    legacy = game.get("play_time")
    if isinstance(legacy, int) and legacy > 0:
        return legacy, legacy
    return None


def _matches_time(game: dict[str, Any], time_filter: DirectoryTime | None) -> bool:
    if not time_filter:
        return True
    duration = _duration_range(game)
    if duration is None:
        return False
    minimum, maximum = duration
    if time_filter == "30-":
        return minimum <= 30 and maximum >= 1
    if time_filter == "30-60":
        return minimum <= 60 and maximum >= 30
    if time_filter == "60-120":
        return minimum <= 120 and maximum >= 60
    return maximum >= 120


def _sort_key(game: dict[str, Any], sort: DirectorySort):
    if sort == "title":
        return _normalize(str(game.get("title_ja") or game.get("title") or ""))
    if sort == "year":
        return int(game.get("published_year") or 0)
    if sort == "play_time":
        duration = _duration_range(game)
        return duration[0] if duration else 10**9
    return str(game.get("created_at") or "")


def _project_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        **result,
        "data": [project_directory_summary(game) for game in result["data"]],
    }


async def _project_evidence(result: dict[str, Any]) -> dict[str, Any]:
    if supabase.is_local() or not result["data"]:
        return result
    projected = await anyio.to_thread.run_sync(project_metadata_evidence, result["data"])
    return {**result, "data": projected}


def _filter_rows(
    rows: list[dict[str, Any]],
    *,
    players: str | None,
    time_filter: DirectoryTime | None,
    tier: str | None,
) -> list[dict[str, Any]]:
    return [
        game
        for game in rows
        if not should_hide_game_from_search(str(game.get("slug") or ""))
        and _matches_players(game, players)
        and _matches_time(game, time_filter)
        and (not tier or game.get("strategy_tier") == tier)
    ]


def _query_ranked_search_results(
    rows: list[dict[str, Any]],
    *,
    players: str | None,
    time_filter: DirectoryTime | None,
    tier: str | None,
    sort: DirectorySort,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    """Filter canonical ranked search results without replacing relevance with recent order."""
    filtered = _filter_rows(rows, players=players, time_filter=time_filter, tier=tier)
    if sort != "recent":
        reverse = sort == "year"
        filtered.sort(key=lambda game: _sort_key(game, sort), reverse=reverse)
    return _project_result({"data": filtered[offset : offset + limit], "total": len(filtered)})


def _query_local(
    *,
    q: str | None,
    players: str | None,
    time_filter: DirectoryTime | None,
    tier: str | None,
    sort: DirectorySort,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    rows = local_db.list_recent(limit=50000, offset=0)["data"]
    filtered = [
        game
        for game in rows
        if not should_hide_game_from_search(str(game.get("slug") or ""))
        and _matches_query(game, q or "")
        and _matches_players(game, players)
        and _matches_time(game, time_filter)
        and (not tier or game.get("strategy_tier") == tier)
    ]
    reverse = sort in {"recent", "year"}
    filtered.sort(key=lambda game: _sort_key(game, sort), reverse=reverse)
    return _project_result({"data": filtered[offset : offset + limit], "total": len(filtered)})


async def list_directory_games(
    *,
    q: str | None = None,
    players: str | None = None,
    time_filter: DirectoryTime | None = None,
    tier: str | None = None,
    sort: DirectorySort = "recent",
    limit: int = 48,
    offset: int = 0,
) -> dict[str, Any]:
    """Return one filtered directory page without loading the full catalog into the browser."""
    if q and q.strip():
        ranked = await supabase.search(q.strip())
        result = _query_ranked_search_results(
            ranked,
            players=players,
            time_filter=time_filter,
            tier=tier,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return await _project_evidence(result)

    if supabase.is_local():
        local_db.init_db()
        return _query_local(
            q=None,
            players=players,
            time_filter=time_filter,
            tier=tier,
            sort=sort,
            limit=limit,
            offset=offset,
        )

    def _q() -> dict[str, Any]:
        query = supabase._get_client().table("games").select("*", count="exact")

        for excluded_slug in sorted(EXCLUDED_GAME_SLUGS):
            query = query.neq("slug", excluded_slug)

        if players:
            if players == "5+":
                query = query.gte("max_players", 5)
            else:
                player_count = int(players)
                query = query.lte("min_players", player_count).gte("max_players", player_count)

        if time_filter == "30-":
            query = query.lte("play_time_min_minutes", 30).gte("play_time_max_minutes", 1)
        elif time_filter == "30-60":
            query = query.lte("play_time_min_minutes", 60).gte("play_time_max_minutes", 30)
        elif time_filter == "60-120":
            query = query.lte("play_time_min_minutes", 120).gte("play_time_max_minutes", 60)
        elif time_filter == "120+":
            query = query.gte("play_time_max_minutes", 120)

        if tier:
            query = query.eq("strategy_tier", tier)

        if sort == "title":
            query = query.order("title_ja", desc=False, nullsfirst=False).order("title", desc=False, nullsfirst=False)
        elif sort == "year":
            query = query.order("published_year", desc=True, nullsfirst=False)
        elif sort == "play_time":
            query = query.order("play_time_min_minutes", desc=False, nullsfirst=False).order(
                "play_time_max_minutes", desc=False, nullsfirst=False
            )
        else:
            query = query.order("created_at", desc=True, nullsfirst=False)

        result = query.range(offset, offset + limit - 1).execute()
        return _project_result({"data": result.data, "total": result.count or 0})

    result = await anyio.to_thread.run_sync(_q)
    return await _project_evidence(result)