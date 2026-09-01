import logging
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

import httpx

logger = logging.getLogger("core.read_retry")

_P = ParamSpec("_P")
_R = TypeVar("_R")


def run_supabase_read(
    operation: Callable[_P, _R],
    *args: _P.args,
    retry_delay_seconds: float = 0.1,
    **kwargs: _P.kwargs,
) -> _R:
    """Retry one proven transient Supabase read transport failure, then fail loudly."""
    try:
        return operation(*args, **kwargs)
    except httpx.RemoteProtocolError:
        logger.warning("Supabase read transport disconnected; retrying once")
        time.sleep(retry_delay_seconds)
        return operation(*args, **kwargs)
