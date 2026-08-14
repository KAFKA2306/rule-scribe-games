from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import anyio

from app.core.supabase import _get_client


class ListNotFoundError(RuntimeError):
    pass


class GameNotFoundError(RuntimeError):
    pass


class DuplicateMembershipError(RuntimeError):
    pass


class InvalidReorderError(RuntimeError):
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

    async def list_lists(self, owner_id: str) -> list[dict[str, Any]]:
        def _q():
            return (
                _get_client()
                .table("user_lists")
                .select("id,name,visibility,system_key,created_at,updated_at")
                .eq("owner_id", owner_id)
                .order("created_at")
                .execute()
                .data
            )
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
            user_list = self._owned_list(client, owner_id, list_id)
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
        return await anyio.to_thread.run_sync(_q)

    async def rename_list(self, owner_id: str, list_id: str, name: str) -> dict[str, Any]:
        def _q():
            client = _get_client()
            self._owned_list(client, owner_id, list_id)
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
            self._owned_list(client, owner_id, list_id)
            client.table("user_lists").delete().eq("id", list_id).eq("owner_id", owner_id).execute()
        await anyio.to_thread.run_sync(_q)

    async def add_item(self, owner_id: str, list_id: str, game_id: str) -> dict[str, Any]:
        def _q():
            client = _get_client()
            self._owned_list(client, owner_id, list_id)
            game_rows = (
                client.table("games")
                .select("id,slug,title,title_ja,image_url")
                .eq("id", game_id)
                .limit(1)
                .execute()
                .data
            )
            if not game_rows:
                raise GameNotFoundError(game_id)
            game = game_rows[0]
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
            last = (
                client.table("user_list_items")
                .select("position")
                .eq("list_id", list_id)
                .order("position", desc=True)
                .limit(1)
                .execute()
                .data
            )
            position = int(last[0]["position"]) + 1 if last else 0
            title_snapshot = str(game.get("title_ja") or game.get("title") or game_id)
            try:
                item = (
                    client.table("user_list_items")
                    .insert({
                        "list_id": list_id,
                        "game_id": game_id,
                        "game_title_snapshot": title_snapshot,
                        "position": position,
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


list_service = ListService()
