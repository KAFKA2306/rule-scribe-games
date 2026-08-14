import pytest
from pydantic import ValidationError

from app.routers import lists
from app.services.list_service import DuplicateMembershipError


USER_A = {"id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}
LIST_ID = "aaaaaaaa-0000-4000-8000-000000000001"
GAME_ID = "11111111-1111-4111-8111-111111111111"
ITEM_ID = "aaaaaaaa-1000-4000-8000-000000000001"


class FakeListService:
    def __init__(self):
        self.calls = []
        self.duplicate = False

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
        return {"id": list_id, "name": name}

    async def delete_list(self, owner_id, list_id):
        self.calls.append(("delete", owner_id, list_id))

    async def add_item(self, owner_id, list_id, game_id):
        self.calls.append(("add", owner_id, list_id, game_id))
        if self.duplicate:
            raise DuplicateMembershipError(game_id)
        return {"id": ITEM_ID, "list_id": list_id, "game_id": game_id}

    async def remove_item(self, owner_id, list_id, item_id):
        self.calls.append(("remove", owner_id, list_id, item_id))

    async def reorder(self, owner_id, list_id, item_ids):
        self.calls.append(("reorder", owner_id, list_id, item_ids))


def test_list_payloads_forbid_user_supplied_owner_id():
    with pytest.raises(ValidationError):
        lists.UserListCreate(name="Favorites", owner_id=USER_A["id"])


def test_item_payloads_forbid_user_supplied_owner_id():
    with pytest.raises(ValidationError):
        lists.UserListItemAdd(game_id=GAME_ID, owner_id=USER_A["id"])


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


def test_missing_verified_user_id_fails_closed():
    with pytest.raises(lists.HTTPException) as exc:
        lists._owner_id({})
    assert exc.value.status_code == 401
