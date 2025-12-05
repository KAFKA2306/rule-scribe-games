from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
import json
import logging
import asyncio
import httpx
import re
import os
import unicodedata
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import yaml
from pathlib import Path
from fastapi import HTTPException, BackgroundTasks
from app.core.supabase import supabase_repository
from app.core.gemini import GeminiClient
from app.utils.affiliate import amazon_search_url
from app.utils.logger import log_audit
import uuid

logger = logging.getLogger(__name__)

_gemini = GeminiClient()
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
_AMAZON_DOMAINS = ("amazon.co.jp", "amazon.com")
_AUDIT_FIELDS = set(_FIELD_KEYS + ["summary", "rules_content", "description", "official_url", "amazon_url", "image_url", "audio_url"])


def _load_prompt(key: str) -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "prompts.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    parts = key.split(".")
    current = data
    for part in parts:
        current = current[part]
    return str(current).strip()


def _slugify(text: str) -> str:
    """Best-effort ASCII kebab-case slug."""
    if not text:
        return "game"
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "game"


def _ensure_amazon_tag(url: str) -> str:
    """Ensure amazon URL contains affiliate tag when configured."""
    tracking_id = os.getenv("AMAZON_TRACKING_ID")
    if not tracking_id or tracking_id.strip() == "":
        return url
    tracking_id = tracking_id.strip()
    parsed = urlparse(url)
    if not any(d in parsed.netloc for d in _AMAZON_DOMAINS):
        return url
    qs = parse_qs(parsed.query)
    if qs.get("tag", [""])[0] == tracking_id:
        return url
    qs["tag"] = tracking_id
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def _validate_game_payload(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not data or not isinstance(data, dict):
        return ["payload_missing_or_invalid"]

    for required in ["title", "summary", "rules_content"]:
        if not data.get(required):
            errors.append(f"{required}_missing")

    if not (data.get("title_ja") or data.get("title_en")):
        errors.append("title_translation_missing")

    int_fields = ["min_players", "max_players", "play_time", "min_age", "published_year"]
    for field in int_fields:
        if field in data and data[field] is not None and not isinstance(data[field], int):
            errors.append(f"{field}_not_int")

    return errors


def _normalize_confidence(data_confidence: Dict[str, Any]) -> Dict[str, float]:
    normalized: Dict[str, float] = {}
    for key in _FIELD_KEYS:
        val = data_confidence.get(key) if isinstance(data_confidence, dict) else 0.0
        try:
            normalized[key] = float(val)
        except Exception:
            normalized[key] = 0.0
    return normalized


async def _run_critic(
    query: str,
    draft_json: Dict[str, Any],
    data_confidence: Dict[str, Any],
    issues: List[Dict[str, Any]],
    context_str: str,
    fix_requests: Optional[List[str]] = None,
    protected_fields: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], List[str], List[str], List[str]]:
    prompt = _load_prompt("metadata_critic.improve").format(
        query=query,
        draft_json=json.dumps(draft_json, ensure_ascii=False),
        data_confidence=json.dumps(data_confidence, ensure_ascii=False),
        issues=json.dumps(issues, ensure_ascii=False),
        context=context_str,
        fix_requests=json.dumps(fix_requests or [], ensure_ascii=False),
        protected_fields=json.dumps(protected_fields or [], ensure_ascii=False),
    )
    result = await _gemini.generate_structured_json(prompt)
    data = result.get("data") if isinstance(result, dict) else result
    notes = result.get("notes", []) if isinstance(result, dict) else []
    unresolved = result.get("unresolved_issues", []) if isinstance(result, dict) else []
    changed = result.get("changed_fields", []) if isinstance(result, dict) else []

    if notes:
        logger.info("Metadata critic notes: %s", notes)
    if unresolved:
        logger.warning("Metadata critic unresolved: %s", unresolved)
    if changed:
        logger.info("Metadata critic changed_fields: %s", changed)

    return data or {}, notes, unresolved, changed


async def generate_metadata(query: str, current_game_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
                parts.append(f"[{i}] {r.get('title')} ({r.get('title_ja')}): {r.get('summary')}")
            context_str = "\n".join(parts)

    # ---------- 1st pass: generator ----------
    draft_prompt = _load_prompt("metadata_generator.generate").format(
        query=query, context=context_str
    )
    gen_start = datetime.now(timezone.utc)
    draft = await _gemini.generate_structured_json(draft_prompt)
    gen_end = datetime.now(timezone.utc)
    generator_attempts = getattr(_gemini, "last_attempts", 1)
    if isinstance(draft, dict) and "error" in draft:
        return draft

    draft_data = draft.get("data", draft if isinstance(draft, dict) else {})
    data_confidence_raw = draft.get("data_confidence", {}) if isinstance(draft, dict) else {}
    data_confidence = _normalize_confidence(data_confidence_raw)
    issues = draft.get("issues", []) if isinstance(draft, dict) else []
    protected_fields = [k for k, v in data_confidence.items() if v >= 0.7]
    logger.info("First pass (generator) done for %s — protected_fields=%s", query, protected_fields)

    # ---------- 2nd pass: critic ----------
    critic_start = datetime.now(timezone.utc)
    final_data, notes, unresolved, changed_fields = await _run_critic(
        query=query,
        draft_json=draft_data,
        data_confidence=data_confidence,
        issues=issues,
        context_str=context_str,
        protected_fields=protected_fields,
    )
    critic_end = datetime.now(timezone.utc)
    critic_attempts = getattr(_gemini, "last_attempts", 1)

    validation_errors = _validate_game_payload(final_data)

    if validation_errors or unresolved:
        fix_requests = validation_errors + unresolved
        final_data, notes2, unresolved2, changed_fields2 = await _run_critic(
            query=query,
            draft_json=final_data,
            data_confidence=data_confidence,
            issues=issues,
            context_str=context_str,
            fix_requests=fix_requests,
            protected_fields=protected_fields,
        )
        notes.extend(notes2)
        unresolved = unresolved2
        if changed_fields2:
            changed_fields = changed_fields2
        validation_errors = _validate_game_payload(final_data)

    if validation_errors:
        logger.error("Validation failed after critic: %s", validation_errors)
        return {"error": "validation_failed", "details": validation_errors}

    if current_game_data:
        final_data.setdefault("id", current_game_data.get("id"))
        final_data.setdefault("slug", current_game_data.get("slug"))
        final_data["data_version"] = current_game_data.get("data_version", 0) + 1

    if not final_data.get("slug"):
        final_data["slug"] = _slugify(final_data.get("title") or query)

    final_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    end_ts = datetime.now(timezone.utc)

    # Structured audit log for local runs
    log_audit(
        action="generate_and_critic",
        run_id=run_id,
        slug=final_data.get("slug"),
        before=current_game_data,
        after=final_data,
        audit_fields=_AUDIT_FIELDS,
        extra={
            "query": query,
            "data_version_before": current_game_data.get("data_version") if current_game_data else None,
            "data_version_after": final_data.get("data_version"),
            "issues": issues,
            "unresolved": unresolved,
            "notes": notes,
            "protected_fields": protected_fields,
            "changed_fields": changed_fields,
            "generator_attempts": generator_attempts,
            "critic_attempts": critic_attempts,
            "latency_ms_total": int((end_ts - start_ts).total_seconds() * 1000),
            "latency_ms_generator": int((gen_end - gen_start).total_seconds() * 1000),
            "latency_ms_critic": int((critic_end - critic_start).total_seconds() * 1000),
            "summary_len": len((final_data.get("summary") or "")),
            "rules_len": len((final_data.get("rules_content") or "")),
        },
    )

    return final_data


async def resolve_external_links(game: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
    run_id = uuid.uuid4().hex
    before_game = game.copy()
    if not force and not _should_resolve_links(game):
        return game
    
    current_hint = {
        k: game.get(k)
        for k in ["title", "title_ja", "published_year", "official_url", "amazon_url", "image_url"]
    }
    prompt = _load_prompt("link_resolve.resolve").format(
        title=game.get("title"),
        current_json=json.dumps(current_hint, ensure_ascii=False),
    )

    candidates = await _gemini.generate_structured_json(prompt)
    if "error" in candidates:
        return game

    keywords = [
        k.lower()
        for k in [game.get("title"), game.get("title_ja"), game.get("title_en")]
        if k
    ]
    
    updates = {}
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        tasks = []
        for field in ["official_url", "amazon_url", "image_url"]:
            tasks.append(
                _verify_url_candidate(
                    client, field, candidates.get(field), game.get(field), keywords
                )
            )
        results = await asyncio.gather(*tasks)

    for field, best_url in results:
        if best_url and best_url != game.get(field):
            if field == "amazon_url":
                best_url = _ensure_amazon_tag(best_url)
            updates[field] = best_url

    if not updates:
        return game

    merged = game.copy()
    merged.update(updates)
    merged["data_version"] = game.get("data_version", 0) + 1
    merged["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    log_audit(
        action="resolve_links",
        run_id=run_id,
        slug=merged.get("slug"),
        before=before_game,
        after=merged,
        audit_fields=_AUDIT_FIELDS,
        extra={"updated_fields": list(updates.keys())},
    )
    return merged


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
    # For Amazon, always prefer a fresh affiliate search link to ensure availability
    if field == "amazon_url":
        title_hint = keywords[0] if keywords else ""
        affiliate_url = amazon_search_url(title_hint) if title_hint else amazon_search_url("board game")
        if affiliate_url:
            return (field, affiliate_url)
        # if no affiliate id, fall back to provided URLs
        if new_url and new_url != "null":
            if await _is_valid_url(client, new_url, field, keywords):
                return (field, _ensure_amazon_tag(new_url))
        if old_url:
            if await _is_valid_url(client, old_url, field, keywords):
                return (field, _ensure_amazon_tag(old_url))
        return (field, None)

    if new_url and new_url != "null":
        if await _is_valid_url(client, new_url, field, keywords):
            return (field, _ensure_amazon_tag(new_url) if field == "amazon_url" else new_url)
    
    if old_url:
        if await _is_valid_url(client, old_url, field, keywords):
            return (field, _ensure_amazon_tag(old_url) if field == "amazon_url" else old_url)
            
    return (field, None)


async def _is_valid_url(
    client: httpx.AsyncClient, url: str, field: str, keywords: List[str]
) -> bool:
    if not url:
        return False
    
    if field == "amazon_url":
        if not any(d in url for d in _AMAZON_DOMAINS):
            return False
        # ensure affiliate tag if available
        url = _ensure_amazon_tag(url)
        return True  # avoid heavy validation; amazon blocks bots

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

    async def list_recent_games(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        return await self.repository.list_recent(limit=limit, offset=offset)

    async def get_game_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        game = await self.repository.get_by_slug(slug)
        if game:
             await self.repository.increment_view_count(game["id"])
        return game

    async def update_game_content(self, slug: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        game = await self.repository.get_by_slug(slug)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        async def _update_task():
            try:
                query = game.get("title")
                if not query:
                    logger.warning(f"Skipping regeneration for game {game['id']}: No title found.")
                    return

                logger.info(f"Starting metadata generation for game: {query} ({slug})")
                result = await generate_metadata(query, current_game_data=game)
                
                if "error" in result:
                    logger.error(f"Metadata generation failed for {slug}: {result['error']}")
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

    async def create_game_from_query(self, query: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
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
