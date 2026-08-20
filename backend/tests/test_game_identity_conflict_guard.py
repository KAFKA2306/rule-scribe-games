import pytest
from fastapi import HTTPException

from app.routers.games import get_game_details, update_game


class _MutationMustNotRun:
    async def update_game_content(self, *_args, **_kwargs):
        pytest.fail("known identity conflicts must be rejected before regeneration")

    async def update_game_manual(self, *_args, **_kwargs):
        pytest.fail("known identity conflicts must be rejected before manual update")


class _ReadMustNotRun:
    async def get_game_by_slug(self, *_args, **_kwargs):
        pytest.fail("retired mixed identity must be rejected before database read")


@pytest.mark.asyncio
@pytest.mark.parametrize("slug", ["game", "hack-clad"])
async def test_known_identity_conflict_blocks_regeneration(slug: str) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await update_game(
            slug=slug,
            game_update=None,
            regenerate=True,
            fill_missing_only=False,
            editor={"id": "editor"},
            service=_MutationMustNotRun(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Game identity conflict requires reviewed repair before mutation"


@pytest.mark.asyncio
async def test_repaired_mixed_game_slug_is_gone() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_game_details(slug="game", service=_ReadMustNotRun())

    assert exc_info.value.status_code == 410
    assert exc_info.value.detail == "Game record retired after identity repair"
