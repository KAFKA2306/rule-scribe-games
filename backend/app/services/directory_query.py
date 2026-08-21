import re
import unicodedata
from typing import Any, Literal

import anyio

from app.core import local_db, supabase

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


def _matches_time(game: dict[str, Any], time_filter: DirectoryTime | None) -> bool:
    if not time_filter:
        return True
    value = game.get("play_time")
    if not isinstance(value, int) or value <= 0:
        return False
    if time_filter == "30-":
        return value <= 30
    if time_filter == "30-60":
        return 30 < value <= 60
    if time_filter == "60-120":
        return 60 < value <= 120
    return value > 120


def _sort_key(game: dict[str, Any], sort: DirectorySort):
    if sort == "title":
        return _normalize(str(game.get("title_ja") or game.get("title") or ""))
    if sort == "year":
        return int(game.get("published_year") or 0)
    if sort == "play_time":
        value = game.get("play_time")
        return value if isinstance(value, int) and value > 0 else 10**9
    return str(game.get("created_at") or "")


def _query_local(
    *,
    q: str | None,
    players: str | None,
    time_filter: DirectoryTime | None,
    sort: DirectorySort,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    rows = local_db.list_recent(limit=50000, offset=0)["data"]
    filtered = [
        game
        for game in rows
        if _matches_query(game, q or "")
        and _matches_players(game, players)
        and _matches_time(game, time_filter)
    ]
    reverse = sort in {"recent", "year"}
    filtered.sort(key=lambda game: _sort_key(game, sort), reverse=reverse)
    return {"data": filtered[offset : offset + limit], "total": len(filtered)}


async def list_directory_games(
    *,
    q: str | None = None,
    players: str | None = None,
    time_filter: DirectoryTime | None = None,
    sort: DirectorySort = "recent",
    limit: int = 48,
    offset: int = 0,
) -> dict[str, Any]:
    """Return one filtered directory page without loading the full catalog into the browser."""
    if supabase.is_local():
        return _query_local(
            q=q,
            players=players,
            time_filter=time_filter,
            sort=sort,
            limit=limit,
            offset=offset,
        )

    def _q() -> dict[str, Any]:
        query = supabase._get_client().table("games").select("*", count="exact")

        if q and q.strip():
            safe_query = q.strip().replace('"', '\\"')
            term = f"*{safe_query}*"
            query = query.or_(
                ",".join(
                    [
                        f'title.ilike."{term}"',
                        f'title_ja.ilike."{term}"',
                        f'title_en.ilike."{term}"',
                        f'summary.ilike."{term}"',
                        f'description.ilike."{term}"',
                    ]
                )
            )

        if players:
            if players == "5+":
                query = query.gte("max_players", 5)
            else:
                player_count = int(players)
                query = query.lte("min_players", player_count).gte("max_players", player_count)

        if time_filter == "30-":
            query = query.gt("play_time", 0).lte("play_time", 30)
        elif time_filter == "30-60":
            query = query.gt("play_time", 30).lte("play_time", 60)
        elif time_filter == "60-120":
            query = query.gt("play_time", 60).lte("play_time", 120)
        elif time_filter == "120+":
            query = query.gt("play_time", 120)

        if sort == "title":
            query = query.order("title_ja", desc=False, nullsfirst=False).order("title", desc=False, nullsfirst=False)
        elif sort == "year":
            query = query.order("published_year", desc=True, nullsfirst=False)
        elif sort == "play_time":
            query = query.order("play_time", desc=False, nullsfirst=False)
        else:
            query = query.order("created_at", desc=True, nullsfirst=False)

        result = query.range(offset, offset + limit - 1).execute()
        return {"data": result.data, "total": result.count or 0}

    return await anyio.to_thread.run_sync(_q)
