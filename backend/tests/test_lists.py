import httpx
import pytest
from pydantic import ValidationError

from app.routers import lists
from app.services.list_service import DuplicateMembershipError, SystemListMutationError


USER_A = {"id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}
LIST_ID = "aaaaaaaa-0000-4000-8000-000000000001"
GAME_ID = "11111111-1111-4111-8111-111111111111"
ITEM_ID = "aaaaaaaa-1000-4000-8000-000000000001"


class FakeListService:
    def __init__(self):
        self.calls = []
        self.duplicate = False
        self.system_mutation = False

    async def list_lists(self, owner_id):
        self.calls.append(("list", owner_id))
        return []

    async def create_list(self, owner_id, name, visibility):
        self.calls.append(("create", owner_id, name, visibility))
        return {"id": LIST_ID, "owner_id": owner_id, "name": name, "visibility": visibility}

    async def get_list(self, owner_id, list_id):
        self.calls.append(("get", owner_id, list_id))
        return {"id": list_id, "name": "Favorites", "items": []}

    async def rename_list(self, owner_id, list_id, name):
        self.calls.append(("rename", owner_id, list_id, name))
        if self.system_mutation:
            raise SystemListMutationError(list_id)
        return {"id": list_id, "name": name}

    async def delete_list(self, owner_id, list_id):
        self.calls.append(("delete", owner_id, list_id))
        if self.system_mutation:
            raise SystemListMutationError(list_id)

    async def add_item(self, owner_id, list_id, game_id):
        self.calls.append(("add", owner_id, list_id, game_id))
        if self.duplicate:
            raise DuplicateMembershipError(game_id)
        return {"id": ITEM_ID, "list_id": list_id, "game_id": game_id}

    async def remove_item(self, owner_id, list_id, item_id):
        self.calls.append(("remove", owner_id, list_id, item_id))

    async def reorder(self, owner_id, list_id, item_ids):
        self.calls.append(("reorder", owner_id, list_id, item_ids))

    async def get_owned_collection(self, owner_id):
        self.calls.append(("owned-list", owner_id))
        return {"id": None, "owner_id": owner_id, "name": "所持ゲーム", "system_key": "owned", "items": []}

    async def owned_status(self, owner_id, game_id):
        self.calls.append(("owned-status", owner_id, game_id))
        return {"owned": False, "item_id": None, "created_at": None}

    async def set_owned(self, owner_id, game_id):
        self.calls.append(("set-owned", owner_id, game_id))
        return {"owned": True, "created": len([c for c in self.calls if c[0] == "set-owned"]) == 1}

    async def remove_owned(self, owner_id, game_id):
        self.calls.append(("remove-owned", owner_id, game_id))
        return {"owned": False, "removed": True}


def test_list_payloads_forbid_user_supplied_owner_id():
    with pytest.raises(ValidationError):
        lists.UserListCreate(name="Favorites", owner_id=USER_A["id"])


def test_item_payloads_forbid_user_supplied_owner_id():
    with pytest.raises(ValidationError):
        lists.UserListItemAdd(game_id=GAME_ID, owner_id=USER_A["id"])


@pytest.mark.asyncio
async def test_list_index_returns_503_for_transport_failure():
    class FailingListService:
        async def list_lists(self, owner_id):
            assert owner_id == USER_A["id"]
            raise httpx.RemoteProtocolError("Server disconnected")

    with pytest.raises(lists.HTTPException) as exc:
        await lists.list_user_lists(user=USER_A, service=FailingListService())

    assert exc.value.status_code == 503
    assert exc.value.detail == "リストを一時的に取得できません。時間をおいて再試行してください。"


@pytest.mark.asyncio
async def test_create_list_uses_only_verified_request_user():
    service = FakeListService()
    payload = lists.UserListCreate(name="  Favorites  ")
    result = await lists.create_user_list(payload, user=USER_A, service=service)
    assert result["owner_id"] == USER_A["id"]
    assert service.calls == [("create", USER_A["id"], "Favorites", "private")]


@pytest.mark.asyncio
async def test_add_item_uses_verified_owner_and_canonical_game_id():
    service = FakeListService()
    payload = lists.UserListItemAdd(game_id=GAME_ID)
    await lists.add_user_list_item(LIST_ID, payload, user=USER_A, service=service)
    assert service.calls == [("add", USER_A["id"], LIST_ID, GAME_ID)]


@pytest.mark.asyncio
async def test_duplicate_membership_returns_conflict():
    service = FakeListService()
    service.duplicate = True
    payload = lists.UserListItemAdd(game_id=GAME_ID)
    with pytest.raises(lists.HTTPException) as exc:
        await lists.add_user_list_item(LIST_ID, payload, user=USER_A, service=service)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_reorder_uses_verified_owner_and_full_item_order():
    service = FakeListService()
    payload = lists.UserListReorder(item_ids=[ITEM_ID])
    await lists.reorder_user_list(LIST_ID, payload, user=USER_A, service=service)
    assert service.calls == [("reorder", USER_A["id"], LIST_ID, [ITEM_ID])]


@pytest.mark.asyncio
async def test_owned_collection_and_status_use_verified_owner():
    service = FakeListService()
    collection = await lists.get_owned_games(user=USER_A, service=service)
    status_result = await lists.get_owned_game_status(GAME_ID, user=USER_A, service=service)
    assert collection["system_key"] == "owned"
    assert status_result["owned"] is False
    assert service.calls == [
        ("owned-list", USER_A["id"]),
        ("owned-status", USER_A["id"], GAME_ID),
    ]


@pytest.mark.asyncio
async def test_owned_game_put_is_idempotent_contract_with_canonical_game_id():
    service = FakeListService()
    first = await lists.set_owned_game(GAME_ID, user=USER_A, service=service)
    second = await lists.set_owned_game(GAME_ID, user=USER_A, service=service)
    assert first == {"owned": True, "created": True}
    assert second == {"owned": True, "created": False}
    assert service.calls == [
        ("set-owned", USER_A["id"], GAME_ID),
        ("set-owned", USER_A["id"], GAME_ID),
    ]


@pytest.mark.asyncio
async def test_remove_owned_game_is_scoped_to_verified_owner():
    service = FakeListService()
    result = await lists.remove_owned_game(GAME_ID, user=USER_A, service=service)
    assert result == {"owned": False, "removed": True}
    assert service.calls == [("remove-owned", USER_A["id"], GAME_ID)]


@pytest.mark.asyncio
async def test_system_list_cannot_be_renamed_or_deleted_via_custom_list_api():
    service = FakeListService()
    service.system_mutation = True
    with pytest.raises(lists.HTTPException) as rename_exc:
        await lists.rename_user_list(LIST_ID, lists.UserListRename(name="renamed"), user=USER_A, service=service)
    with pytest.raises(lists.HTTPException) as delete_exc:
        await lists.delete_user_list(LIST_ID, user=USER_A, service=service)
    assert rename_exc.value.status_code == 409
    assert delete_exc.value.status_code == 409


def test_missing_verified_user_id_fails_closed():
    with pytest.raises(lists.HTTPException) as exc:
        lists._owner_id({})
    assert exc.value.status_code == 401
