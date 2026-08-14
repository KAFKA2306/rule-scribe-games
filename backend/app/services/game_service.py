import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core import supabase
from app.core.gemini import GeminiClient
from app.core.llm_manager import LLMKeyRotator
from app.models import GeneratedGameMetadata
from app.prompts.prompts import PROMPTS
from app.utils.affiliate import amazon_search_url
from app.utils.slugify import slugify

logger = logging.getLogger("agents.game_service")
_gemini = GeminiClient()
_key_rotator = LLMKeyRotator("GEMINI_API_KEY")
_pipeline = None  # Lazy load in method
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
        try:
            rows = await supabase.search(query)
            if rows:
                context = "\n".join(
                    f"[{i}] {r.get('title', 'Unknown')!s}: {r.get('summary', '')!s}" for i, r in enumerate(rows[:3], 1)
                )
                logger.info(f"Context retrieved from DB for {query}")
        except Exception as e:
            logger.warning(f"Could not retrieve context from DB: {e}")

    if not context:
        context = "New game discovery. No existing context in database. Use general knowledge and search grounding."
        logger.info(f"Using default context for {query}")

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
    def __init__(self):
        self.use_local = True
        try:
            supabase._get_client()
            self.use_local = False
            logger.info("Supabase connected. Using cloud DB.")
        except Exception:
            logger.warning("Supabase not configured. Falling back to local SQLite.")
            from app.core import local_db

            local_db.init_db()

    async def search_games(self, query: str) -> list[dict[str, Any]]:
        return await supabase.search(query)

    async def list_recent_games(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return await supabase.list_recent(limit=limit, offset=offset)

    async def get_game_by_slug(self, slug: str) -> dict[str, Any] | None:
        return await supabase.get_by_slug(slug)

    async def create_game_from_query(self, query: str) -> dict[str, Any]:
        """Create one unverified canonical game after the DB-first search path misses."""
        query = query.strip()
        if not query:
            raise ValueError("Game query must not be blank")

        # Recheck immediately before generation to avoid duplicate writes when requests race.
        existing = await supabase.search(query)
        if existing:
            return existing[0]

        metadata = await generate_metadata(query)
        title = str(metadata.get("title_ja") or metadata.get("title") or query).strip()
        generated_slug = str(metadata.get("slug") or slugify(title) or "").strip()
        if not generated_slug:
            generated_slug = f"game-{uuid.uuid4().hex[:8]}"

        slug_owner = await supabase.get_by_slug(generated_slug)
        if slug_owner:
            return slug_owner

        metadata.pop("id", None)
        metadata["slug"] = generated_slug
        metadata["title"] = metadata.get("title") or title
        metadata["created_at"] = metadata.get("created_at") or datetime.now(UTC).isoformat()
        metadata["updated_at"] = datetime.now(UTC).isoformat()
        metadata["data_version"] = int(metadata.get("data_version", 0) or 0)
        return await supabase.create_unverified_game(metadata)

    async def update_game_content(self, slug: str, fill_missing_only: bool = False) -> dict[str, Any]:
        game = await supabase.get_by_slug(slug)
        if not game:
            raise ValueError(f"Game not found for slug: {slug}")

        title = game.get("title")
        summary = game.get("summary")
        ctx = f"{title!s}: {summary!s}"
        result = await generate_metadata(str(title), ctx)
        merged = _merge_fields(game, result, fill_missing_only)

        if not merged.get("id") or not slug:
            raise ValueError("Corrupt game record: missing id or slug")

        # Canonical identity never changes through content regeneration.
        merged["id"], merged["slug"] = game["id"], slug
        merged["work_id"] = game.get("work_id")
        merged["identity_status"] = game.get("identity_status", "unverified")
        merged["data_version"] = int(game.get("data_version", 0) or 0) + 1
        out = await supabase.upsert(merged)
        if not out:
            raise RuntimeError(f"Upsert failed for game: {slug}")
        return out[0]

    async def update_game_manual(self, slug: str, updates: dict[str, Any]) -> dict[str, Any]:
        game = await supabase.get_by_slug(slug)
        if not game:
            raise ValueError(f"Game not found for slug: {slug}")

        # Identity fields are not mutable through the generic content endpoint.
        protected = {"id", "slug", "work_id", "identity_status"}
        safe_updates = {key: value for key, value in updates.items() if key not in protected}
        merged = {**game, **safe_updates}
        merged["updated_at"] = datetime.now(UTC).isoformat()
        out = await supabase.upsert(merged)
        if not out:
            raise RuntimeError(f"Update failed for game: {slug}")
        return out[0]

    async def generate_with_notebooklm(self, query: str, generate_infographics: bool = True) -> dict[str, Any]:
        """Legacy internal pipeline. Public catalog creation uses create_game_from_query()."""
        global _pipeline
        if _pipeline is None:
            from app.services.pipeline_orchestrator import PipelineOrchestrator

            _pipeline = PipelineOrchestrator()
        result = await _pipeline.process_game_rules(query, generate_infographics=generate_infographics)
        if not result:
            raise RuntimeError(f"NotebookLM generation failed for: {query}")
        return result


def _merge_fields(original: dict[str, Any], incoming: dict[str, Any], fill_missing_only: bool) -> dict[str, Any]:
    if not fill_missing_only:
        return {**original, **incoming}
    merged = dict(original)
    for key, value in incoming.items():
        current = merged.get(key)
        is_missing = current is None or (isinstance(current, str) and current.strip() == "")
        if is_missing:
            merged[key] = value
        if key == "structured_data" and (current is None or current == {}):
            merged[key] = value
    return merged
