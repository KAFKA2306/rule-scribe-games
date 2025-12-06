from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import yaml
from pathlib import Path
from fastapi import HTTPException, BackgroundTasks
from app.core.gemini import GeminiClient
from app.core import supabase
from app.utils.slugify import slugify

_gemini = GeminiClient()
_REQUIRED = ["title", "summary", "rules_content"]


def _load_prompt(key: str) -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "prompts.yaml"
    data = yaml.safe_load(open(path, encoding="utf-8"))
    for part in key.split("."):
        data = data[part]
    return str(data).strip()


def _validate(data: Dict[str, Any]) -> bool:
    return all(data.get(f) for f in _REQUIRED)


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
        return result


    result = await _improve_metadata(query, result, context)

    data = result.get("data", result) if isinstance(result, dict) else {}

    if not _validate(data):
        return {"error": "validation_failed"}

    if not data.get("slug"):
        data["slug"] = slugify(data.get("title") or query)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    from app.utils.affiliate import amazon_search_url
    data["amazon_url"] = amazon_search_url(data.get("title") or query)

    return data


async def _improve_metadata(
    query: str, draft: Dict[str, Any], context: str
) -> Dict[str, Any]:
    data = draft.get("data", draft)
    confidence = draft.get("data_confidence", {})
    issues = draft.get("issues", [])
    

    protected = [
        k for k, v in confidence.items() 
        if isinstance(v, (int, float)) and v >= 0.7
    ]

    prompt = _load_prompt("metadata_critic.improve").format(
        query=query,
        draft_json=json.dumps(data, ensure_ascii=False),
        data_confidence=json.dumps(confidence, ensure_ascii=False),
        issues=json.dumps(issues, ensure_ascii=False),
        context=context,
        fix_requests=json.dumps([], ensure_ascii=False),
        protected_fields=json.dumps(protected, ensure_ascii=False),
    )
    
    critic_output = await _gemini.generate_structured_json(prompt)
    

    if not isinstance(critic_output, dict) or "data" not in critic_output:
        return draft
        
    return critic_output


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
        self, slug: str, bg: BackgroundTasks, fill_missing_only: bool = False
    ) -> Dict[str, Any]:
        game = await supabase.get_by_slug(slug)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        async def _task():
            ctx = json.dumps(game, ensure_ascii=False)
            result = await generate_metadata(game.get("title"), ctx)
            if "error" not in result:
                merged = _merge_fields(game, result, fill_missing_only)
                merged["id"], merged["slug"] = game["id"], slug
                merged["data_version"] = game.get("data_version", 0) + 1
                await supabase.upsert(merged)

        bg.add_task(_task)
        return {"status": "accepted"}

    async def create_game_from_query(
        self, query: str, bg: BackgroundTasks
    ) -> Dict[str, Any]:
        result = await generate_metadata(query)
        if "error" in result:
            return {}
        out = await supabase.upsert(result)
        return out[0] if out else {}


def _merge_fields(
    original: Dict[str, Any], incoming: Dict[str, Any], fill_missing_only: bool
) -> Dict[str, Any]:
    if not fill_missing_only:
        return {**original, **incoming}

    merged = dict(original)
    for key, value in incoming.items():
        current = merged.get(key)
        # Treat None or empty string as missing; keep zeros and False as intentional values.
        is_missing = current is None or (isinstance(current, str) and current.strip() == "")
        if is_missing:
            merged[key] = value
        # Shallow merge for structured_data if it's missing or empty dict
        if key == "structured_data":
            if current is None or current == {}:
                merged[key] = value
    return merged
