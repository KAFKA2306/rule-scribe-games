import pytest

from app.services import game_service
from app.services.game_service import GameIdentityConflictError, GameService


@pytest.fixture
def verified_game() -> dict[str, object]:
    return {
        "id": "game-1",
        "slug": "first-game",
        "work_id": "work-1",
        "identity_status": "verified",
        "title": "First Game",
        "title_ja": "ファーストゲーム",
        "title_en": "First Game",
        "summary": "old summary",
        "data_version": 1,
    }


@pytest.mark.asyncio
async def test_regeneration_rejects_existing_cross_work_title_before_generation(monkeypatch, verified_game) -> None:
    writes: list[dict[str, object]] = []

    async def _get_by_slug(_slug: str):
        return dict(verified_game)

    async def _upsert(payload):
        writes.append(payload)
        return [payload]

    async def _context():
        games = [
            dict(verified_game),
            {
                "id": "game-2",
                "slug": "second-game",
                "work_id": "work-2",
                "title": "First Game",
            },
        ]
        aliases = [
            {"game_id": "game-1", "title": "First Game"},
            {"game_id": "game-1", "title": "ファーストゲーム"},
            {"game_id": "game-2", "title": "First Game"},
        ]
        return games, aliases

    async def _generate_must_not_run(*_args, **_kwargs):
        pytest.fail("incoherent title identity must be rejected before generation")

    monkeypatch.setattr(game_service.supabase, "get_by_slug", _get_by_slug)
    monkeypatch.setattr(game_service.supabase, "upsert", _upsert)
    monkeypatch.setattr(game_service, "_load_identity_coherence_context", _context)
    monkeypatch.setattr(game_service, "generate_metadata", _generate_must_not_run)

    service = GameService.__new__(GameService)
    with pytest.raises(GameIdentityConflictError, match="title_alias_bound_to_multiple_works"):
        await service.update_game_content("first-game")

    assert writes == []


@pytest.mark.asyncio
async def test_regeneration_accepts_titles_bound_only_to_current_work(monkeypatch, verified_game) -> None:
    writes: list[dict[str, object]] = []

    async def _get_by_slug(_slug: str):
        return dict(verified_game)

    async def _upsert(payload):
        writes.append(payload)
        return [payload]

    async def _context():
        return [dict(verified_game)], [
            {"game_id": "game-1", "title": "First Game"},
            {"game_id": "game-1", "title": "ファーストゲーム"},
        ]

    async def _generate(_query: str, _context: str):
        return {"summary": "new summary"}

    monkeypatch.setattr(game_service.supabase, "get_by_slug", _get_by_slug)
    monkeypatch.setattr(game_service.supabase, "upsert", _upsert)
    monkeypatch.setattr(game_service, "_load_identity_coherence_context", _context)
    monkeypatch.setattr(game_service, "generate_metadata", _generate)

    service = GameService.__new__(GameService)
    result = await service.update_game_content("first-game")

    assert result["summary"] == "new summary"
    assert result["data_version"] == 2
    assert len(writes) == 1
