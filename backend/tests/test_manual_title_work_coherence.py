import pytest

from app.services import game_service
from app.services.game_service import GameIdentityConflictError, GameService


@pytest.fixture
def existing_game() -> dict[str, object]:
    return {
        "id": "game-1",
        "slug": "first-game",
        "work_id": "work-1",
        "identity_status": "verified",
        "title": "First Game",
        "title_ja": "ファーストゲーム",
        "title_en": "First Game",
        "summary": "old summary",
    }


@pytest.mark.asyncio
async def test_manual_title_update_rejects_title_bound_to_another_work(monkeypatch, existing_game) -> None:
    writes: list[dict[str, object]] = []

    async def _get_by_slug(_slug: str):
        return dict(existing_game)

    async def _upsert(payload):
        writes.append(payload)
        return [payload]

    async def _context():
        games = [
            dict(existing_game),
            {
                "id": "game-2",
                "slug": "second-game",
                "work_id": "work-2",
                "title": "Second Game",
            },
        ]
        aliases = [
            {"game_id": "game-1", "title": "First Game"},
            {"game_id": "game-1", "title": "ファーストゲーム"},
            {"game_id": "game-2", "title": "Second Game"},
        ]
        return games, aliases

    monkeypatch.setattr(game_service.supabase, "get_by_slug", _get_by_slug)
    monkeypatch.setattr(game_service.supabase, "upsert", _upsert)
    monkeypatch.setattr(game_service, "_load_identity_coherence_context", _context)

    service = GameService.__new__(GameService)
    with pytest.raises(GameIdentityConflictError, match="title_bound_to_different_work"):
        await service.update_game_manual("first-game", {"title_en": "Second Game"})

    assert writes == []


@pytest.mark.asyncio
async def test_manual_title_update_accepts_verified_alias_for_same_work(monkeypatch, existing_game) -> None:
    writes: list[dict[str, object]] = []

    async def _get_by_slug(_slug: str):
        return dict(existing_game)

    async def _upsert(payload):
        writes.append(payload)
        return [payload]

    async def _context():
        games = [dict(existing_game)]
        aliases = [
            {"game_id": "game-1", "title": "First Game"},
            {"game_id": "game-1", "title": "ファーストゲーム"},
            {"game_id": "game-1", "title": "First Game Revised"},
        ]
        return games, aliases

    monkeypatch.setattr(game_service.supabase, "get_by_slug", _get_by_slug)
    monkeypatch.setattr(game_service.supabase, "upsert", _upsert)
    monkeypatch.setattr(game_service, "_load_identity_coherence_context", _context)

    service = GameService.__new__(GameService)
    result = await service.update_game_manual("first-game", {"title_en": "First Game Revised"})

    assert result["title_en"] == "First Game Revised"
    assert len(writes) == 1


@pytest.mark.asyncio
async def test_non_title_manual_update_does_not_require_identity_context(monkeypatch, existing_game) -> None:
    async def _get_by_slug(_slug: str):
        return dict(existing_game)

    async def _upsert(payload):
        return [payload]

    async def _context_must_not_run():
        pytest.fail("non-title updates must not load title identity context")

    monkeypatch.setattr(game_service.supabase, "get_by_slug", _get_by_slug)
    monkeypatch.setattr(game_service.supabase, "upsert", _upsert)
    monkeypatch.setattr(game_service, "_load_identity_coherence_context", _context_must_not_run)

    service = GameService.__new__(GameService)
    result = await service.update_game_manual("first-game", {"summary": "new summary"})

    assert result["summary"] == "new summary"
