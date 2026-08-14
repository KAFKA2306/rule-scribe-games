from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.routers.auth import get_current_user
from app.services.list_service import (
    DuplicateMembershipError,
    GameNotFoundError,
    InvalidReorderError,
    ListNotFoundError,
    ListService,
    list_service,
)

router = APIRouter()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserListCreate(StrictModel):
    name: str = Field(min_length=1, max_length=80)
    visibility: Literal["private", "public"] = "private"

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class UserListRename(StrictModel):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class UserListItemAdd(StrictModel):
    game_id: UUID


class UserListReorder(StrictModel):
    item_ids: list[UUID]


def get_list_service() -> ListService:
    return list_service


def _owner_id(user: dict) -> str:
    owner_id = user.get("id")
    if not owner_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verified user id required")
    return str(owner_id)


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List or item not found")


@router.get("/lists")
async def list_user_lists(
    user: dict = Depends(get_current_user),
    service: ListService = Depends(get_list_service),
):
    return {"lists": await service.list_lists(_owner_id(user))}


@router.post("/lists", status_code=status.HTTP_201_CREATED)
async def create_user_list(
    payload: UserListCreate,
    user: dict = Depends(get_current_user),
    service: ListService = Depends(get_list_service),
):
    return await service.create_list(_owner_id(user), payload.name, payload.visibility)


@router.get("/lists/{list_id}")
async def get_user_list(
    list_id: UUID,
    user: dict = Depends(get_current_user),
    service: ListService = Depends(get_list_service),
):
    try:
        return await service.get_list(_owner_id(user), str(list_id))
    except ListNotFoundError as exc:
        raise _not_found() from exc


@router.patch("/lists/{list_id}")
async def rename_user_list(
    list_id: UUID,
    payload: UserListRename,
    user: dict = Depends(get_current_user),
    service: ListService = Depends(get_list_service),
):
    try:
        return await service.rename_list(_owner_id(user), str(list_id), payload.name)
    except ListNotFoundError as exc:
        raise _not_found() from exc


@router.delete("/lists/{list_id}")
async def delete_user_list(
    list_id: UUID,
    user: dict = Depends(get_current_user),
    service: ListService = Depends(get_list_service),
):
    try:
        await service.delete_list(_owner_id(user), str(list_id))
        return {"status": "deleted"}
    except ListNotFoundError as exc:
        raise _not_found() from exc


@router.post("/lists/{list_id}/items", status_code=status.HTTP_201_CREATED)
async def add_user_list_item(
    list_id: UUID,
    payload: UserListItemAdd,
    user: dict = Depends(get_current_user),
    service: ListService = Depends(get_list_service),
):
    try:
        return await service.add_item(_owner_id(user), str(list_id), str(payload.game_id))
    except ListNotFoundError as exc:
        raise _not_found() from exc
    except GameNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canonical game not found") from exc
    except DuplicateMembershipError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game is already in this list") from exc


@router.delete("/lists/{list_id}/items/{item_id}")
async def remove_user_list_item(
    list_id: UUID,
    item_id: UUID,
    user: dict = Depends(get_current_user),
    service: ListService = Depends(get_list_service),
):
    try:
        await service.remove_item(_owner_id(user), str(list_id), str(item_id))
        return {"status": "deleted"}
    except ListNotFoundError as exc:
        raise _not_found() from exc


@router.put("/lists/{list_id}/order")
async def reorder_user_list(
    list_id: UUID,
    payload: UserListReorder,
    user: dict = Depends(get_current_user),
    service: ListService = Depends(get_list_service),
):
    try:
        await service.reorder(_owner_id(user), str(list_id), [str(item_id) for item_id in payload.item_ids])
        return {"status": "reordered"}
    except ListNotFoundError as exc:
        raise _not_found() from exc
    except InvalidReorderError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must contain every list item exactly once") from exc
