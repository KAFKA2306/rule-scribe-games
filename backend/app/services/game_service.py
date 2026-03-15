import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from app.prompts.prompts import PROMPTS
from app.utils.affiliate import amazon_search_url

from app.core import supabase
from app.core.gemini import GeminiClient
from app.core.llm_manager import LLMKeyRotator
from app.models import GeneratedGameMetadata
from app.services.pipeline_orchestrator import PipelineOrchestrator

logger = logging.getLogger("agents.game_service")
_gemini = GeminiClient()
_key_rotator = LLMKeyRotator("GEMINI_API_KEY")
_pipeline = PipelineOrchestrator()
_REQUIRED = ["title", "summary", "rules_content"]
_ALLOWED_FIELDS = {
    "id",
    "slug",
    "title",
    "title_ja",
    "title_en",
    "description",
    "summary",
    "rules_content",
    "structured_data",
    "source_url",
    "affiliate_urls",
    "view_count",
    "search_count",
    "data_version",
    "is_official",
    "min_players",
    "max_players",
    "play_time",
    "min_age",
    "published_year",
    "image_url",
    "official_url",
    "bgg_url",
    "bga_url",
    "amazon_url",
    "audio_url",
    "created_at",
    "updated_at",
}


def _load_prompt(key: str) -> str:
    data = PROMPTS
    for part in key.split("."):
        data = data[part]
    return str(data).strip()


async def generate_metadata(query: str, context: str | None = None) -> dict[str, Any]:
    task_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(
        "task_start",
        extra={
            "agent": "GameMetadata",
            "task_id": task_id,
            "query": query,
            "available_keys": _key_rotator.get_status()["total_keys"],
        },
    )

    if not context:
        rows = await supabase.search(query)
        context = (
            "\n".join(
                f"[{i}] {r.get('title', 'Unknown')!s}: {r.get('summary', '')!s}" for i, r in enumerate(rows[:3], 1)
            )
            if rows
            else "No matches."
        )
        logger.info(
            "context_retrieved",
            extra={
                "task_id": task_id,
                "similar_games": len(rows) if rows else 0,
            },
        )

    prompt = _load_prompt("metadata_generator.generate").format(query=query, context=context)

    key = _key_rotator.get_next_key()
    key_index = _key_rotator.keys.index(key) + 1

    logger.info(
        "attempt_start",
        extra={
            "task_id": task_id,
            "attempt": 1,
            "key_index": key_index,
        },
    )

    attempt_start = time.time()
    result = await _gemini.generate_structured_json(prompt, api_key=key)
    attempt_duration = (time.time() - attempt_start) * 1000

    validated_data = GeneratedGameMetadata.model_validate(result)
    logger.info(
        "attempt_success",
        extra={
            "task_id": task_id,
            "duration_ms": int(attempt_duration),
        },
    )

    data = validated_data.model_dump()
    data = {k: v for k, v in data.items() if k in _ALLOWED_FIELDS}
    data["updated_at"] = datetime.now(UTC).isoformat()
    data["amazon_url"] = amazon_search_url(str(data.get("title_ja") or query))

    total_duration = (time.time() - start_time) * 1000
    logger.info(
        "task_complete",
        extra={
            "task_id": task_id,
            "status": "success",
            "total_duration_ms": int(total_duration),
        },
    )
    return data


class GameService:
    async def search_games(self, query: str) -> list[dict[str, Any]]:
        return await supabase.search(query)

    async def list_recent_games(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        return await supabase.list_recent(limit=limit, offset=offset)

    async def get_game_by_slug(self, slug: str) -> dict[str, Any] | None:
        game = await supabase.get_by_slug(slug)
        if game:
            await supabase.increment_view_count(str(game["id"]))
        return game

    async def update_game_content(self, slug: str, fill_missing_only: bool = False) -> dict[str, Any]:
        game = await supabase.get_by_slug(slug)
        if not game:
            return {}
        title = game.get("title")
        summary = game.get("summary")
        ctx = f"{title!s}: {summary!s}"
        result = await generate_metadata(str(title), ctx)
        merged = _merge_fields(game, result, fill_missing_only)
        merged["id"], merged["slug"] = game["id"], slug
        merged["data_version"] = int(game.get("data_version", 0) or 0) + 1
        out = await supabase.upsert(merged)
        return out[0] if out else {}

    async def create_game_from_query(self, query: str) -> dict[str, Any]:
        result = await generate_metadata(query)
        out = await supabase.upsert(result)
        return out[0] if out else {}

    async def update_game_manual(self, slug: str, updates: dict[str, Any]) -> dict[str, Any]:
        game = await supabase.get_by_slug(slug)
        if not game:
            return {}
        merged = {**game, **updates}
        merged["updated_at"] = datetime.now(UTC).isoformat()
        out = await supabase.upsert(merged)
        return out[0] if out else {}

    async def generate_with_notebooklm(self, query: str) -> dict[str, Any]:
        result = await _pipeline.process_game_rules(query)
        out = await supabase.upsert(result)
        return out[0] if out else {}


def _merge_fields(original: dict[str, Any], incoming: dict[str, Any], fill_missing_only: bool) -> dict[str, Any]:
    if not fill_missing_only:
        return {**original, **incoming}
    merged = dict(original)
    for key, value in incoming.items():
        current = merged.get(key)
        is_missing = current is None or (isinstance(current, str) and current.strip() == "")
        if is_missing:
            merged[key] = value
        if key == "structured_data":
            if current is None or current == {}:
                merged[key] = value
    return merged
