from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.prompts.prompts import PROMPTS

from fastapi import HTTPException
from app.core.gemini import GeminiClient
from app.core import supabase
from app.utils.slugify import slugify

_gemini = GeminiClient()
_REQUIRED = ["title", "summary", "rules_content"]

def _load_prompt(key: str) -> str:
    data = PROMPTS
    for part in key.split("."):
        data = data[part]
    return str(data).strip()


def _validate(data: Dict[str, Any]) -> None:
    if not all(data.get(f) for f in _REQUIRED):
        raise ValueError(f"Validation failed. Missing required fields: {_REQUIRED}")


async def generate_metadata(
    query: str, context: Optional[str] = None
) -> Dict[str, Any]:
    if not context:
        rows = await supabase.search(query)
        context = (
            "\n".join(
                f"[{i}] {r.get('title')}: {r.get('summary')}"
                for i, r in enumerate(rows[:3], 1)
            )
            if rows
            else "No matches."
        )

    prompt = _load_prompt("metadata_generator.generate").format(
        query=query, context=context
    )
    result = await _gemini.generate_structured_json(prompt)

    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"Gemini error: {result['error']}")

    data = result.get("data", result) if isinstance(result, dict) else {}

    _validate(data)

    if not data.get("slug"):
        data["slug"] = slugify(data.get("title") or query)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    from app.utils.affiliate import amazon_search_url

    data["amazon_url"] = amazon_search_url(data.get("title_ja") or query)

    return data


class GameService:
    async def search_games(self, query: str) -> List[Dict[str, Any]]:
        return await supabase.search(query)

    async def list_recent_games(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        return await supabase.list_recent(limit=limit, offset=offset)

    async def get_game_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        game = await supabase.get_by_slug(slug)
        if game:
            await supabase.increment_view_count(game["id"])
        return game

    async def update_game_content(
        self, slug: str, fill_missing_only: bool = False
    ) -> Dict[str, Any]:
        game = await supabase.get_by_slug(slug)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        ctx = f"{game.get('title')}: {game.get('summary')}"
        result = await generate_metadata(game.get("title"), ctx)

        merged = _merge_fields(game, result, fill_missing_only)
        merged["id"], merged["slug"] = game["id"], slug
        merged["data_version"] = game.get("data_version", 0) + 1

        out = await supabase.upsert(merged)
        return out[0] if out else {}

    async def create_game_from_query(self, query: str) -> Dict[str, Any]:
        result = await generate_metadata(query)
        out = await supabase.upsert(result)
        return out[0] if out else {}

    async def update_game_manual(
        self, slug: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        game = await supabase.get_by_slug(slug)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        merged = {**game, **updates}
        merged["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Remove keys that might be in game but not valid for upsert if schema has changed,
        # or if we are strict. But usually Supabase handles it or we should be careful.
        # For now, we trust the model and existing data.

        out = await supabase.upsert(merged)
        return out[0] if out else {}


def _merge_fields(
    original: Dict[str, Any], incoming: Dict[str, Any], fill_missing_only: bool
) -> Dict[str, Any]:
    if not fill_missing_only:
        return {**original, **incoming}

    merged = dict(original)
    for key, value in incoming.items():
        current = merged.get(key)
        is_missing = current is None or (
            isinstance(current, str) and current.strip() == ""
        )
        if is_missing:
            merged[key] = value
        if key == "structured_data":
            if current is None or current == {}:
                merged[key] = value
    return merged
