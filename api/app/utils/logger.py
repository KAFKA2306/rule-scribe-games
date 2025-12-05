import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional


def configure_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
    return logging.getLogger()


configure_logging()


def log_audit(
    action: str,
    run_id: str,
    slug: Optional[str],
    before: Optional[Dict[str, Any]],
    after: Dict[str, Any],
    audit_fields: Iterable[str],
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    record = {
        "action": action,
        "run_id": run_id,
        "slug": slug,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "extra": extra or {},
    }
    logging.info("AUDIT %s", json.dumps(record, ensure_ascii=False))
