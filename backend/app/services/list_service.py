from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import anyio

from app.core.supabase import _get_client


OWNED_SYSTEM_KEY = "owned"
OWNED_LIST_NAME = "所持ゲーム"


class ListNotFoundError(RuntimeError):
    pass


class GameNotFoundError(RuntimeError):
    pass


class DuplicateMembershipError(RuntimeError):
    pass


class InvalidReorderError(RuntimeError):
    pass


class SystemListMutationError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ListService:
    @staticmethod
    def _owned_list(client, owner_id: str, list_id: str) -> dict[str, Any]:
        rows = (
            client.table("user_lists")
            .select("*")
            .eq("id", list_id)
            .eq("owner_id", owner_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            raise ListNotFoundError(list_id)
        return rows[0]

    @staticmethod
    def _system_list(client, owner_id: str, system_key: str) -> dict[str, Any] | None:
        rows = (
            client.table("user_lists")
            .select("*")
            .eq("owner_id", owner_id)
            .eq("system_key", system_key)
            .limit(1)
            .execute()
            .data
        )
        return rows[0] if rows else None

    @staticmethod
    def _canonical_game(client, game_id: str) -> dict[str, Any]:
        rows = (
            client.table("games")
            .select("id,slug,title,title_ja,image_url")
            .eq("id", game_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            raise GameNotFoundError(game_id)
        return rows[0]

    @staticmethod
    def _next_position(client, list_id: str) -> int:
        rows = (
            client.table("user_list_items")
            .select("position")
            .eq("list_id", list_id)
            .order("position", desc=True)
            .limit(1)
            .execute()
            .data
        )
        return int(rows[0]["position"]) + 1 if rows else 0

    @staticmethod
    def _detail(client, user_list: dict[str, Any]) -> dict[str, Any]:
        list_id = str(user_list["id"])
        items = (
            client.table("user_list_items")
            .select("id,list_id,game_id,game_title_snapshot,position,created_at,updated_at")
            .eq("list_id", list_id)
            .order("position")
            .order("created_at")
            .execute()
            .data
        )
        game_ids = [item["game_id"] for item in items if item.get("game_id")]
        games: list[dict[str, Any]] = []
        if game_ids:
            games = (
                client.table("games")
                .select("id,slug,title,title_ja,image_url")
                .in_("id", game_ids)
                .execute()
                .data
            )
        games_by_id = {game["id"]: game for game in games}
        normalized_items = []
        for item in items:
            game = games_by_id.get(item.get("game_id"))
            normalized_items.append({**item, "game": game, "unavailable": game is None})
        return {**user_list, "items": normalized_items}

    @classmethod
    def _ensure_owned_system_list(cls, client, owner_id: str) -> dict[str, Any]:
        existing = cls._system_list(client, owner_id, OWNED_SYSTEM_KEY)
        if existing:
            return existing
        try:
            return (
                client.table("user_lists")
                .insert({
                    "owner_id": owner_id,
                    "name": OWNED_LIST_NAME,
                    "visibility": "private",
                    "system_key": OWNED_SYSTEM_KEY,
                })
                .execute()
                .data[0]
            )
        except Exception as exc:
            if "23505" not in str(exc) and "duplicate" not in str(exc).lower():
                raise
            existing = cls._system_list(client, owner_id, OWNED_SYSTEM_KEY)
            if existing:
                return existing
            raise

    async def list_lists(self, owner_id: str) -> list[dict[str, Any]]:
        def _q():
            rows = (
                _get_client()
                .table("user_lists")
                .select("id,name,visibility,system_key,created_at,updated_at")
                .eq("owner_id", owner_id)
                .order("created_at")
                .execute()
                .data
            )
            return [row for row in rows if row.get("system_key") is None]
        return await anyio.to_thread.run_sync(_q)

    async def create_list(self, owner_id: str, name: str, visibility: str) -> dict[str, Any]:
        def _q():
            return (
                _get_client()
                .table("user_lists")
                .insert({"owner_id": owner_id, "name": name, "visibility": visibility})
                .execute()
                .data[0]
            )
        return await anyio.to_thread.run_sync(_q)

    async def get_list(self, owner_id: str, list_id: str) -> dict[str, Any]:
        def _q():
            client = _get_client()
            return self._detail(client, self._owned_list(client, owner_id, list_id))
        return await anyio.to_thread.run_sync(_q)

    async def rename_list(self, owner_id: str, list_id: str, name: str) -> dict[str, Any]:
        def _q():
            client = _get_client()
            user_list = self._owned_list(client, owner_id, list_id)
            if user_list.get("system_key") is not None:
                raise SystemListMutationError(list_id)
            rows = (
                client.table("user_lists")
                .update({"name": name, "updated_at": _now()})
                .eq("id", list_id)
                .eq("owner_id", owner_id)
                .execute()
                .data
            )
            if not rows:
                raise ListNotFoundError(list_id)
            return rows[0]
        return await anyio.to_thread.run_sync(_q)

    async def delete_list(self, owner_id: str, list_id: str) -> None:
        def _q():
            client = _get_client()
            user_list = self._owned_list(client, owner_id, list_id)
            if user_list.get("system_key") is not None:
                raise SystemListMutationError(list_id)
            client.table("user_lists").delete().eq("id", list_id).eq("owner_id", owner_id).execute()
        await anyio.to_thread.run_sync(_q)

    async def add_item(self, owner_id: str, list_id: str, game_id: str) -> dict[str, Any]:
        def _q():
            client = _get_client()
            self._owned_list(client, owner_id, list_id)
            game = self._canonical_game(client, game_id)
            existing = (
                client.table("user_list_items")
                .select("id")
                .eq("list_id", list_id)
                .eq("game_id", game_id)
                .limit(1)
                .execute()
                .data
            )
            if existing:
                raise DuplicateMembershipError(game_id)
            title_snapshot = str(game.get("title_ja") or game.get("title") or game_id)
            try:
                item = (
                    client.table("user_list_items")
                    .insert({
                        "list_id": list_id,
                        "game_id": game_id,
                        "game_title_snapshot": title_snapshot,
                        "position": self._next_position(client, list_id),
                    })
                    .execute()
                    .data[0]
                )
            except Exception as exc:
                if "23505" in str(exc) or "duplicate" in str(exc).lower():
                    raise DuplicateMembershipError(game_id) from exc
                raise
            client.table("user_lists").update({"updated_at": _now()}).eq("id", list_id).eq("owner_id", owner_id).execute()
            return {**item, "game": game, "unavailable": False}
        return await anyio.to_thread.run_sync(_q)

    async def remove_item(self, owner_id: str, list_id: str, item_id: str) -> None:
        def _q():
            client = _get_client()
            self._owned_list(client, owner_id, list_id)
            rows = (
                client.table("user_list_items")
                .select("id")
                .eq("id", item_id)
                .eq("list_id", list_id)
                .limit(1)
                .execute()
                .data
            )
            if not rows:
                raise ListNotFoundError(item_id)
            client.table("user_list_items").delete().eq("id", item_id).eq("list_id", list_id).execute()
            client.table("user_lists").update({"updated_at": _now()}).eq("id", list_id).eq("owner_id", owner_id).execute()
        await anyio.to_thread.run_sync(_q)

    async def reorder(self, owner_id: str, list_id: str, item_ids: list[str]) -> None:
        def _q():
            client = _get_client()
            self._owned_list(client, owner_id, list_id)
            try:
                client.rpc(
                    "reorder_owned_list_items",
                    {"p_owner_id": owner_id, "p_list_id": list_id, "p_item_ids": item_ids},
                ).execute()
            except Exception as exc:
                if "invalid_item_order" in str(exc) or "22023" in str(exc):
                    raise InvalidReorderError(list_id) from exc
                raise
        await anyio.to_thread.run_sync(_q)

    async def get_owned_collection(self, owner_id: str) -> dict[str, Any]:
        def _q():
            client = _get_client()
            owned_list = self._system_list(client, owner_id, OWNED_SYSTEM_KEY)
            if not owned_list:
                return {
                    "id": None,
                    "owner_id": owner_id,
                    "name": OWNED_LIST_NAME,
                    "visibility": "private",
                    "system_key": OWNED_SYSTEM_KEY,
                    "created_at": None,
                    "updated_at": None,
                    "items": [],
                }
            return self._detail(client, owned_list)
        return await anyio.to_thread.run_sync(_q)

    async def owned_status(self, owner_id: str, game_id: str) -> dict[str, Any]:
        def _q():
            client = _get_client()
            owned_list = self._system_list(client, owner_id, OWNED_SYSTEM_KEY)
            if not owned_list:
                return {"owned": False, "item_id": None, "created_at": None}
            rows = (
                client.table("user_list_items")
                .select("id,created_at")
                .eq("list_id", str(owned_list["id"]))
                .eq("game_id", game_id)
                .limit(1)
                .execute()
                .data
            )
            if not rows:
                return {"owned": False, "item_id": None, "created_at": None}
            return {"owned": True, "item_id": rows[0]["id"], "created_at": rows[0].get("created_at")}
        return await anyio.to_thread.run_sync(_q)

    async def set_owned(self, owner_id: str, game_id: str) -> dict[str, Any]:
        def _q():
            client = _get_client()
            game = self._canonical_game(client, game_id)
            owned_list = self._ensure_owned_system_list(client, owner_id)
            list_id = str(owned_list["id"])
            existing = (
                client.table("user_list_items")
                .select("id,list_id,game_id,game_title_snapshot,position,created_at,updated_at")
                .eq("list_id", list_id)
                .eq("game_id", game_id)
                .limit(1)
                .execute()
                .data
            )
            if existing:
                return {"owned": True, "created": False, "item": {**existing[0], "game": game, "unavailable": False}}

            title_snapshot = str(game.get("title_ja") or game.get("title") or game_id)
            try:
                item = (
                    client.table("user_list_items")
                    .insert({
                        "list_id": list_id,
                        "game_id": game_id,
                        "game_title_snapshot": title_snapshot,
                        "position": self._next_position(client, list_id),
                    })
                    .execute()
                    .data[0]
                )
                created = True
            except Exception as exc:
                if "23505" not in str(exc) and "duplicate" not in str(exc).lower():
                    raise
                rows = (
                    client.table("user_list_items")
                    .select("id,list_id,game_id,game_title_snapshot,position,created_at,updated_at")
                    .eq("list_id", list_id)
                    .eq("game_id", game_id)
                    .limit(1)
                    .execute()
                    .data
                )
                if not rows:
                    raise
                item = rows[0]
                created = False
            client.table("user_lists").update({"updated_at": _now()}).eq("id", list_id).eq("owner_id", owner_id).execute()
            return {"owned": True, "created": created, "item": {**item, "game": game, "unavailable": False}}
        return await anyio.to_thread.run_sync(_q)

    async def remove_owned(self, owner_id: str, game_id: str) -> dict[str, Any]:
        def _q():
            client = _get_client()
            owned_list = self._system_list(client, owner_id, OWNED_SYSTEM_KEY)
            if not owned_list:
                return {"owned": False, "removed": False}
            list_id = str(owned_list["id"])
            rows = (
                client.table("user_list_items")
                .select("id")
                .eq("list_id", list_id)
                .eq("game_id", game_id)
                .limit(1)
                .execute()
                .data
            )
            if not rows:
                return {"owned": False, "removed": False}
            client.table("user_list_items").delete().eq("id", rows[0]["id"]).eq("list_id", list_id).execute()
            client.table("user_lists").update({"updated_at": _now()}).eq("id", list_id).eq("owner_id", owner_id).execute()
            return {"owned": False, "removed": True}
        return await anyio.to_thread.run_sync(_q)


list_service = ListService()
