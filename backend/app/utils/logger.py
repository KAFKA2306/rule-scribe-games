import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional


def configure_logging(level: int = logging.INFO, *, json_mode: bool = False) -> logging.Logger:
    """Configure root logger once; return it."""
    logger = logging.getLogger()
    if logger.handlers:
        return logger  # already configured

    handler = logging.StreamHandler(sys.stdout)
    if json_mode:
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


# Initialize root logger in json mode for AUDIT lines; idempotent if already set elsewhere.
configure_logging(json_mode=True)


def diff_records(old: Optional[Dict[str, Any]], new: Dict[str, Any], audit_fields: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    """Return field-level before/after differences limited to audit_fields."""
    if new is None:
        return {}
    fields = set(audit_fields or [])
    if not fields:
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    keys = set(new.keys())
    if old:
        keys |= set(old.keys())

    for k in keys:
        if k not in fields:
            continue
        before = old.get(k) if old else None
        after = new.get(k)
        if before != after:
            out[k] = {"before": before, "after": after}
    return out


def log_audit(
    action: str,
    run_id: str,
    slug: Optional[str],
    before: Optional[Dict[str, Any]],
    after: Dict[str, Any],
    audit_fields: Iterable[str],
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Emit a structured audit log line to the standard logger."""
    logger = logging.getLogger(__name__)
    try:
        record = {
            "action": action,
            "run_id": run_id,
            "slug": slug,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "diff": diff_records(before, after, audit_fields),
        }
        if extra:
            record.update(extra)
        logger.info("AUDIT %s", json.dumps(record, ensure_ascii=False))
    except Exception:
        logger.exception("Failed to write audit log")
