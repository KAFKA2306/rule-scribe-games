import httpx
import pytest

from app.routers import lists


USER = {"id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}


class FailingListService:
    async def list_lists(self, owner_id):
        assert owner_id == USER["id"]
        raise httpx.RemoteProtocolError("Server disconnected")


@pytest.mark.asyncio
async def test_list_index_returns_503_for_transport_failure():
    with pytest.raises(lists.HTTPException) as exc:
        await lists.list_user_lists(user=USER, service=FailingListService())

    assert exc.value.status_code == 503
    assert exc.value.detail == "リストを一時的に取得できません。時間をおいて再試行してください。"
