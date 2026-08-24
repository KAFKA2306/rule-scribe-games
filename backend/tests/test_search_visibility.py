import pytest

from app.core import supabase
from app.services.directory_query import _filter_rows
from app.services.game_service import GameService
from app.services.search_visibility import has_known_identity_conflict, should_hide_game_from_search


@pytest.mark.asyncio
async def test_canonical_search_hides_retired_records_and_keeps_verified_games(monkeypatch) -> None:
    async def _search(_query: str):
        return [
            {"slug": "game", "title": "mixed historical row"},
            {"slug": "hackclad", "title": "legacy HacKClaD duplicate"},
            {"slug": "hack-clad", "title": "HacKClaD"},
            {"slug": "3", "title": "3秒トライ！"},
            {"slug": "3-second-try", "title": "3秒トライ！"},
            {"slug": "little-town-builders", "title": "リトルタウンビルダーズ"},
            {"slug": "little-town", "title": "リトルタウンビルダーズ"},
        ]

    monkeypatch.setattr(supabase, "search", _search)
    service = GameService.__new__(GameService)

    results = await service.search_games("game")

    assert [row["slug"] for row in results] == ["hack-clad", "3-second-try", "little-town"]
    assert has_known_identity_conflict("game") is True
    assert has_known_identity_conflict("hackclad") is True
    assert has_known_identity_conflict("3") is True
    assert has_known_identity_conflict("little-town-builders") is True
    assert has_known_identity_conflict("hack-clad") is False
    assert has_known_identity_conflict("3-second-try") is False
    assert has_known_identity_conflict("little-town") is False


def test_directory_filter_uses_same_identity_visibility_contract() -> None:
    rows = [
        {"slug": "game", "title": "mixed historical row"},
        {"slug": "hackclad", "title": "legacy HacKClaD duplicate"},
        {"slug": "hack-clad", "title": "HacKClaD"},
        {"slug": "3", "title": "3秒トライ！"},
        {"slug": "3-second-try", "title": "3秒トライ！"},
        {"slug": "little-town-builders", "title": "リトルタウンビルダーズ"},
        {"slug": "little-town", "title": "リトルタウンビルダーズ"},
    ]

    filtered = _filter_rows(rows, players=None, time_filter=None, tier=None)

    assert [row["slug"] for row in filtered] == ["hack-clad", "3-second-try", "little-town"]
    assert should_hide_game_from_search("game") is True
    assert should_hide_game_from_search("hackclad") is True
    assert should_hide_game_from_search("3") is True
    assert should_hide_game_from_search("little-town-builders") is True
    assert should_hide_game_from_search("hack-clad") is False
    assert should_hide_game_from_search("3-second-try") is False
    assert should_hide_game_from_search("little-town") is False
