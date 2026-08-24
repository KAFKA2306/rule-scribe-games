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
            {"slug": "heart-of-crown", "title": "Heart of Crown 2nd Edition"},
            {"slug": "heart-of-crown-2nd-edition", "title": "Heart of Crown 2nd Edition"},
            {"slug": "icefall", "title": "アイスフォール"},
            {"slug": "ice-fall", "title": "ICE FALL"},
        ]

    monkeypatch.setattr(supabase, "search", _search)
    service = GameService.__new__(GameService)

    results = await service.search_games("game")

    assert [row["slug"] for row in results] == [
        "hack-clad",
        "3-second-try",
        "little-town",
        "heart-of-crown-2nd-edition",
        "ice-fall",
    ]
    for slug in ("game", "hackclad", "3", "little-town-builders", "heart-of-crown", "icefall"):
        assert has_known_identity_conflict(slug) is True
    for slug in ("hack-clad", "3-second-try", "little-town", "heart-of-crown-2nd-edition", "ice-fall"):
        assert has_known_identity_conflict(slug) is False


def test_directory_filter_uses_same_identity_visibility_contract() -> None:
    rows = [
        {"slug": "game", "title": "mixed historical row"},
        {"slug": "hackclad", "title": "legacy HacKClaD duplicate"},
        {"slug": "hack-clad", "title": "HacKClaD"},
        {"slug": "3", "title": "3秒トライ！"},
        {"slug": "3-second-try", "title": "3秒トライ！"},
        {"slug": "little-town-builders", "title": "リトルタウンビルダーズ"},
        {"slug": "little-town", "title": "リトルタウンビルダーズ"},
        {"slug": "heart-of-crown", "title": "Heart of Crown 2nd Edition"},
        {"slug": "heart-of-crown-2nd-edition", "title": "Heart of Crown 2nd Edition"},
        {"slug": "icefall", "title": "アイスフォール"},
        {"slug": "ice-fall", "title": "ICE FALL"},
    ]

    filtered = _filter_rows(rows, players=None, time_filter=None, tier=None)

    assert [row["slug"] for row in filtered] == [
        "hack-clad",
        "3-second-try",
        "little-town",
        "heart-of-crown-2nd-edition",
        "ice-fall",
    ]
    for slug in ("game", "hackclad", "3", "little-town-builders", "heart-of-crown", "icefall"):
        assert should_hide_game_from_search(slug) is True
    for slug in ("hack-clad", "3-second-try", "little-town", "heart-of-crown-2nd-edition", "ice-fall"):
        assert should_hide_game_from_search(slug) is False
