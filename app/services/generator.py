from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import json
import logging
import yaml
from pathlib import Path
from app.core.gemini import GeminiClient

logger = logging.getLogger(__name__)

_gemini = GeminiClient()
_FIELD_KEYS = [
    "slug",
    "title",
    "title_ja",
    "title_en",
    "summary",
    "rules_content",
    "description",
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
    "video_url",
]


def _load_prompt(key: str) -> str:
    path = Path(__file__).resolve().parent.parent / "prompts" / "prompts.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    parts = key.split(".")
    current = data
    for part in parts:
        current = current[part]
    return str(current).strip()


def _validate_game_payload(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not data or not isinstance(data, dict):
        return ["payload_missing_or_invalid"]

    for required in ["title", "summary", "rules_content"]:
        if not data.get(required):
            errors.append(f"{required}_missing")

    if not (data.get("title_ja") or data.get("title_en")):
        errors.append("title_translation_missing")

    int_fields = [
        "min_players",
        "max_players",
        "play_time",
        "min_age",
        "published_year",
    ]
    for field in int_fields:
        if (
            field in data
            and data[field] is not None
            and not isinstance(data[field], int)
        ):
            errors.append(f"{field}_not_int")

    return errors


def _normalize_confidence(data_confidence: Dict[str, Any]) -> Dict[str, float]:
    normalized: Dict[str, float] = {}
    for key in _FIELD_KEYS:
        val = data_confidence.get(key) if isinstance(data_confidence, dict) else 0.0
        normalized[key] = float(val if val is not None else 0.0)
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


async def generate_metadata_core(query: str, context_str: str) -> Dict[str, Any]:
    draft_prompt = _load_prompt("metadata_generator.generate").format(
        query=query, context=context_str
    )
    gen_start = datetime.now(timezone.utc)
    draft = await _gemini.generate_structured_json(draft_prompt)
    gen_end = datetime.now(timezone.utc)

    if isinstance(draft, dict) and "error" in draft:
        return {"error": draft["error"], "details": draft}

    draft_data = draft.get("data", draft if isinstance(draft, dict) else {})
    data_confidence_raw = (
        draft.get("data_confidence", {}) if isinstance(draft, dict) else {}
    )
    data_confidence = _normalize_confidence(data_confidence_raw)
    issues = draft.get("issues", []) if isinstance(draft, dict) else []
    protected_fields = [k for k, v in data_confidence.items() if v >= 0.7]
    logger.info(
        "First pass (generator) done for %s — protected_fields=%s",
        query,
        protected_fields,
    )

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

    return {
        "final_data": final_data,
        "metrics": {
            "latency_ms_generator": int((gen_end - gen_start).total_seconds() * 1000),
            "latency_ms_critic": int(
                (critic_end - critic_start).total_seconds() * 1000
            ),
            "issues": issues,
            "unresolved": unresolved,
            "notes": notes,
            "changed_fields": changed_fields,
        },
    }
