from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import json
import logging
import httpx
import re
from fastapi import HTTPException, BackgroundTasks
from api.app.core.supabase import supabase_repository
from api.app.services import generator
from api.app.utils.affiliate import amazon_search_url, ensure_amazon_tag, _AMAZON_DOMAINS
from api.app.utils.slugify import slugify
from api.app.utils.logger import log_audit
import uuid

logger = logging.getLogger(__name__)

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
_COOLDOWN_DAYS = 30
_FIELD_KEYS = [
    "slug",
    "title",
    "title_ja",
    "title_en",
    "summary",
    "rules_content",
    "image_url",
    "min_players",
    "max_players",
    "play_time",
    "min_age",
    "published_year",
    "official_url",
    "bgg_url",
    "bga_url",
    "amazon_url",
]
_AUDIT_FIELDS = set(
    _FIELD_KEYS
    + [
        "summary",
        "rules_content",
        "description",
        "official_url",
        "amazon_url",
        "image_url",
        "audio_url",
    ]
)


async def generate_metadata(
    query: str, current_game_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    run_id = uuid.uuid4().hex
    start_ts = datetime.now(timezone.utc)

    if current_game_data:
        context_str = json.dumps(current_game_data, ensure_ascii=False, indent=2)
    else:
        existing_rows = await supabase_repository.search(query)
        context_str = "No local database matches found."
        if existing_rows:
            parts = []
            for i, r in enumerate(existing_rows[:3], 1):
                parts.append(
                    f"[{i}] {r.get('title')} ({r.get('title_ja')}): {r.get('summary')}"
                )
            context_str = "\n".join(parts)

    gen_result = await generator.generate_metadata_core(query, context_str)

    if "error" in gen_result:
        return gen_result

    final_data = gen_result["final_data"]
    metrics = gen_result["metrics"]

    if current_game_data:
        final_data.setdefault("id", current_game_data.get("id"))
        final_data.setdefault("slug", current_game_data.get("slug"))
        final_data["data_version"] = current_game_data.get("data_version", 0) + 1

    if not final_data.get("slug"):
        final_data["slug"] = slugify(final_data.get("title") or query)

    final_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    end_ts = datetime.now(timezone.utc)

    log_audit(
        action="generate_and_critic",
        run_id=run_id,
        slug=final_data.get("slug"),
        before=current_game_data,
        after=final_data,
        audit_fields=_AUDIT_FIELDS,
        extra={
            "query": query,
            "data_version_before": current_game_data.get("data_version")
            if current_game_data
            else None,
            "data_version_after": final_data.get("data_version"),
            **metrics,
            "latency_ms_total": int((end_ts - start_ts).total_seconds() * 1000),
            "summary_len": len((final_data.get("summary") or "")),
            "rules_len": len((final_data.get("rules_content") or "")),
        },
    )

    return final_data


async def resolve_external_links(
    game: Dict[str, Any], force: bool = False
) -> Dict[str, Any]:
    if not force and not _should_resolve_links(game):
        return game

    pass

    return game


def _should_resolve_links(game: Dict[str, Any]) -> bool:
    has_links = all(
        [game.get("official_url"), game.get("amazon_url"), game.get("image_url")]
    )
    if has_links:
        updated_at = game.get("updated_at")
        if not updated_at:
            return False

        if isinstance(updated_at, str):
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        else:
            dt = updated_at

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return not (datetime.now(timezone.utc) - dt < timedelta(days=_COOLDOWN_DAYS))
    return True


async def _verify_url_candidate(
    client: httpx.AsyncClient,
    field: str,
    new_url: Optional[str],
    old_url: Optional[str],
    keywords: List[str],
) -> tuple[str, Optional[str]]:
    if field == "amazon_url":
        title_hint = keywords[0] if keywords else ""
        affiliate_url = (
            amazon_search_url(title_hint)
            if title_hint
            else amazon_search_url("board game")
        )
        if affiliate_url:
            return (field, affiliate_url)

        if new_url and new_url != "null":
            if await _is_valid_url(client, new_url, field, keywords):
                return (field, ensure_amazon_tag(new_url))
        if old_url:
            if await _is_valid_url(client, old_url, field, keywords):
                return (field, ensure_amazon_tag(old_url))
        return (field, None)

    if new_url and new_url != "null":
        if await _is_valid_url(client, new_url, field, keywords):
            return (
                field,
                ensure_amazon_tag(new_url) if field == "amazon_url" else new_url,
            )

    if old_url:
        if await _is_valid_url(client, old_url, field, keywords):
            return (
                field,
                ensure_amazon_tag(old_url) if field == "amazon_url" else old_url,
            )

    return (field, None)


async def _is_valid_url(
    client: httpx.AsyncClient, url: str, field: str, keywords: List[str]
) -> bool:
    if not url:
        return False

    if field == "amazon_url":
        if not any(d in url for d in _AMAZON_DOMAINS):
            return False
            return False

        url = ensure_amazon_tag(url)
        return True

    head_resp = await client.head(url, headers={"User-Agent": _USER_AGENT})
    if head_resp.status_code == 200:
        resp = head_resp
    else:
        resp = await client.get(url, headers={"User-Agent": _USER_AGENT})

    if resp.status_code != 200:
        if resp.status_code in [403, 405] and field == "official_url":
            pass
        else:
            return False

    if field == "image_url":
        ct = resp.headers.get("content-type", "").lower()
        return "image/" in ct or "application/octet-stream" in ct

    if not hasattr(resp, "text") or not resp.text:
        resp = await client.get(url, headers={"User-Agent": _USER_AGENT})

    match = re.search("<title>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
    html_title = match.group(1).lower().strip() if match else ""

    return any((k in html_title for k in keywords))


class GameService:
    def __init__(self):
        self.repository = supabase_repository

    async def search_games(self, query: str) -> List[Dict[str, Any]]:
        return await self.repository.search(query)

    async def list_recent_games(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        return await self.repository.list_recent(limit=limit, offset=offset)

    async def get_game_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        game = await self.repository.get_by_slug(slug)
        if game:
            await self.repository.increment_view_count(game["id"])
        return game

    async def update_game_content(
        self, slug: str, background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        game = await self.repository.get_by_slug(slug)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        async def _update_task():
            try:
                query = game.get("title")
                if not query:
                    logger.warning(
                        f"Skipping regeneration for game {game['id']}: No title found."
                    )
                    return

                logger.info(f"Starting metadata generation for game: {query} ({slug})")
                result = await generate_metadata(query, current_game_data=game)

                if "error" in result:
                    logger.error(
                        f"Metadata generation failed for {slug}: {result['error']}"
                    )
                    return

                result["id"] = game["id"]
                result["slug"] = slug

                await self.repository.upsert(result)
                logger.info(f"Metadata updated for {slug}")

                updated_game = await self.repository.get_by_id(game["id"])
                if updated_game:
                    logger.info(f"Resolving links for {slug}")
                    final_data = await resolve_external_links(updated_game, force=True)
                    await self.repository.upsert(final_data)
                    logger.info(f"Regeneration complete for {slug}")
            except Exception as e:
                logger.exception(f"CRITICAL ERROR in _update_task for {slug}: {e}")

        background_tasks.add_task(_update_task)
        return {"status": "accepted", "message": "Regeneration task started"}

    async def create_game_from_query(
        self, query: str, background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        result = await generate_metadata(query)
        if "error" in result:
            return {}

        out = await self.repository.upsert(result)
        if not out:
            return {}

        saved_game = out[0]

        async def _resolve_task():
            final = await resolve_external_links(saved_game, force=True)
            await self.repository.upsert(final)

        background_tasks.add_task(_resolve_task)
        return saved_game
