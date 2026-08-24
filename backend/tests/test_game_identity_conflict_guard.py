import pytest
from fastapi import HTTPException

from app.main import game_seo_page
from app.models import GameUpdate
from app.routers.games import get_game_details, update_game
from app.services.search_visibility import has_known_identity_conflict


class _MutationMustNotRun:
    async def update_game_manual(self, *_args, **_kwargs):
        pytest.fail("known identity conflicts must be rejected before manual update")


class _ReadMustNotRun:
    async def get_game_by_slug(self, *_args, **_kwargs):
        pytest.fail("retired mixed identity must be rejected before database read")


@pytest.mark.asyncio
async def test_known_identity_conflict_blocks_manual_update() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await update_game(
            slug="game",
            game_update=GameUpdate(title="replacement"),
            editor={"id": "editor"},
            service=_MutationMustNotRun(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Game identity conflict requires reviewed repair before mutation"


def test_repaired_hackclad_is_not_kept_in_identity_conflict_registry() -> None:
    assert has_known_identity_conflict("hack-clad") is False


@pytest.mark.asyncio
async def test_repaired_mixed_game_slug_is_gone() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_game_details(slug="game", service=_ReadMustNotRun())

    assert exc_info.value.status_code == 410
    assert exc_info.value.detail == "Game record retired after identity repair"


@pytest.mark.asyncio
async def test_repaired_mixed_game_slug_is_not_rendered_in_ssr(monkeypatch) -> None:
    async def _render_must_not_run(_slug: str):
        pytest.fail("retired mixed identity must be rejected before SSR data read")

    monkeypatch.setattr("app.main.generate_seo_html", _render_must_not_run)

    response = await game_seo_page("game")

    assert response.status_code == 410
    assert "ゲームが見つかりません" in response.body.decode("utf-8")
