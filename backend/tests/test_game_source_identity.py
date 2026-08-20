import pytest

from app.services.game_service import (
    GameIdentityConflictError,
    _validate_manual_source_update,
)


@pytest.mark.asyncio
async def test_source_url_bound_only_to_current_work_is_accepted(monkeypatch) -> None:
    async def _bindings(_url: str) -> set[str]:
        return {"work-a"}

    monkeypatch.setattr("app.services.game_service._load_source_work_bindings", _bindings)

    await _validate_manual_source_update(
        {"work_id": "work-a", "source_url": "https://example.com/old"},
        {"source_url": "https://example.com/new"},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("bindings", "reason"),
    [
        (set(), "source_unbound"),
        ({"work-b"}, "source_bound_to_another_work"),
        ({"work-a", "work-b"}, "source_bound_to_multiple_works"),
    ],
)
async def test_source_url_without_unique_current_work_binding_is_rejected(monkeypatch, bindings, reason) -> None:
    async def _bindings(_url: str) -> set[str]:
        return bindings

    monkeypatch.setattr("app.services.game_service._load_source_work_bindings", _bindings)

    with pytest.raises(GameIdentityConflictError, match=reason):
        await _validate_manual_source_update(
            {"work_id": "work-a", "source_url": "https://example.com/old"},
            {"source_url": "https://example.com/new"},
        )


@pytest.mark.asyncio
async def test_unchanged_source_url_does_not_load_evidence(monkeypatch) -> None:
    async def _must_not_run(_url: str) -> set[str]:
        pytest.fail("unchanged source_url must not query evidence bindings")

    monkeypatch.setattr("app.services.game_service._load_source_work_bindings", _must_not_run)

    await _validate_manual_source_update(
        {"work_id": "work-a", "source_url": "https://example.com/current"},
        {"summary": "updated"},
    )
