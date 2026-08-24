import pytest

from app.core import supabase
from app.services.directory_query import _filter_rows
from app.services.game_service import GameService
from app.services.search_visibility import has_known_identity_conflict, should_hide_game_from_search


@pytest.mark.asyncio
async def test_canonical_search_hides_retired_mixed_identity_but_keeps_repaired_game(monkeypatch) -> None:
    async def _search(_query: str):
        return [
            {"slug": "game", "title": "mixed historical row"},
            {"slug": "hack-clad", "title": "HacKClaD"},
        ]

    monkeypatch.setattr(supabase, "search", _search)
    service = GameService.__new__(GameService)

    results = await service.search_games("hack")

    assert [row["slug"] for row in results] == ["hack-clad"]
    assert has_known_identity_conflict("game") is True
    assert has_known_identity_conflict("hack-clad") is False


def test_directory_filter_uses_same_identity_visibility_contract() -> None:
    rows = [
        {"slug": "game", "title": "mixed historical row"},
        {"slug": "hack-clad", "title": "HacKClaD"},
    ]

    filtered = _filter_rows(rows, players=None, time_filter=None, tier=None)

    assert [row["slug"] for row in filtered] == ["hack-clad"]
    assert should_hide_game_from_search("game") is True
    assert should_hide_game_from_search("hack-clad") is False
