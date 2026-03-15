# Database Infrastructure Troubleshooting: Connection Pool Exhaustion

## Problem Statement

Batch PDF extraction script processing 50+ games hits "connection pool exceeded" errors around game 15-20, hangs, and requires manual process termination.

**Symptoms:**
- Script completes 15-20 games successfully
- Subsequent database calls timeout
- Process must be killed with `SIGKILL`
- No graceful cleanup or connection recycling

---

## Root Cause Analysis

### Primary Issues

#### 1. **Connection Pool Exhaustion via Synchronous-to-Async Mismatch**

**Location:** `app/core/supabase.py` lines 11-17, 31-44

Current implementation:
```python
async def search(query: str) -> list[dict[str, object]]:
    def _q():
        safe_query = query.replace('"', '\\"')
        term = f"*{safe_query}*"
        return _client.table(_TABLE).select("*").or_(f'title.ilike."{term}",description.ilike."{term}"').execute().data

    return await anyio.to_thread.run_sync(_q)
```

**Problem:** Each `anyio.to_thread.run_sync()` call:
- Spawns a new thread for a synchronous Supabase client operation
- The Supabase client (`_client`) is a **global singleton** created at module import time
- In a batch loop (50 iterations), if 10+ operations run concurrently, threads accumulate
- Supabase SDK maintains an internal HTTP connection pool (default: ~10-20 connections)
- When all connections are exhausted, new requests block or timeout

**Why it fails at game 15-20:**
- Each `upsert()`, `search()`, and `get_by_slug()` call spawns a thread
- In batch processing: search → generate → validate → upsert = 3-4 async calls per game
- After ~15 games, 45-60 threads compete for 10-20 connections
- Thread overhead + connection reuse delays cause timeouts

---

#### 2. **Lack of Connection Recycling / Session Management**

The Supabase client is created once at module initialization and never refreshed:
```python
_client = create_client(settings.supabase_url, settings.supabase_key)
```

**Problems:**
- No connection timeout or idle timeout handling
- No explicit pooling configuration (Supabase SDK defaults to minimal pool)
- Long-lived threads don't release connections back to the pool efficiently
- Network interruptions leave zombie connections in the pool

---

#### 3. **Sequential Processing Without Backpressure**

Current batch script (example from `scripts/update_rules_batch1.py`):
```python
for slug, content in UPDATES.items():
    try:
        res = supabase._client.table("games").update({"rules_content": content}).eq("slug", slug).execute()
    except Exception:
        pass
```

**Problems:**
- No rate limiting or throttling
- No waits between requests
- Exception is silently swallowed (violates CDD principle)
- No backoff or retry with exponential delays

---

#### 4. **No Async Concurrency Control**

The service layer (`app/services/game_service.py`) doesn't use semaphores or connection pooling limits:
```python
async def update_game_content(self, slug: str, fill_missing_only: bool = False) -> dict[str, object]:
    game = await supabase.get_by_slug(slug)
    # ... more supabase calls
    merged["data_version"] = int(game.get("data_version", 0) or 0) + 1
    out = await supabase.upsert(merged)
```

If called in a tight loop with `asyncio.gather()`, creates unlimited concurrent tasks.

---

## Diagnostic Steps

### Step 1: Verify Connection Pool Status

```bash
# Check Supabase service health
curl -s "https://$NEXT_PUBLIC_SUPABASE_URL/health" | jq

# Monitor active connections (PostgreSQL side, if you have admin access)
# Connect to Supabase PostgreSQL console and run:
SELECT count(*) as connection_count FROM pg_stat_activity WHERE datname = 'postgres';
SELECT client_addr, state, state_change FROM pg_stat_activity;
```

### Step 2: Check Current Batch Script

List all batch scripts and identify the one causing the issue:
```bash
ls -la /home/kafka/projects/rule-scribe-games/scripts/*batch*.py
ls -la /home/kafka/projects/rule-scribe-games/scripts/add_*.py
ls -la /home/kafka/projects/rule-scribe-games/scripts/update_*.py
```

Identify scripts that:
1. Loop over 50+ games
2. Call Supabase functions without delays
3. Use `asyncio.gather()` without limits
4. Don't implement retry/backoff

### Step 3: Check Thread Pool Configuration

```bash
# Python 3.11+ default: max_workers = (os.cpu_count() or 1) + 4
# On a 4-core system: 8 worker threads
python3 -c "import os; print(f'CPU count: {os.cpu_count()}, default workers: {(os.cpu_count() or 1) + 4}')"
```

If 8 workers × 4-5 supabase calls per game = 32-40 concurrent threads competing for 10-20 connections → deadlock.

### Step 4: Trace Connection Lifecycle

Add debug logging to `app/core/supabase.py`:
```bash
# Enable Supabase SDK debug logs (if available)
export SUPABASE_DEBUG=true
# Run batch script with logging
python -m scripts.your_batch_script 2>&1 | tee batch_debug.log
```

Look for patterns:
```
Thread-1: Acquiring connection...
Thread-2: Acquiring connection...
Thread-3: Waiting for connection (pool exhausted)...
Thread-4: Timeout after 30s
```

---

## Code Fixes

### Fix 1: Add Connection Pool Configuration (Recommended)

Create a new module `app/core/supabase_pool.py`:

```python
import os
from typing import Optional
from supabase import Client, create_client
from app.core.settings import settings

_pool_size = int(os.getenv("SUPABASE_POOL_SIZE", "5"))
_max_overflow = int(os.getenv("SUPABASE_MAX_OVERFLOW", "10"))

class PooledSupabaseClient:
    def __init__(self):
        self._client: Optional[Client] = None
        self._active_connections = 0
        self._max_connections = _pool_size + _max_overflow

    def get_client(self) -> Client:
        if self._client is None:
            self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    def close(self):
        if self._client:
            # Supabase SDK doesn't have explicit close, but we can clear reference
            self._client = None

supabase_pool = PooledSupabaseClient()
```

Replace in `app/core/supabase.py`:
```python
from app.core.supabase_pool import supabase_pool

async def search(query: str) -> list[dict[str, object]]:
    def _q():
        client = supabase_pool.get_client()
        safe_query = query.replace('"', '\\"')
        term = f"*{safe_query}*"
        return client.table(_TABLE).select("*").or_(f'title.ilike."{term}",description.ilike."{term}"').execute().data

    return await anyio.to_thread.run_sync(_q)
```

---

### Fix 2: Add Semaphore to Limit Concurrent Connections

In `app/core/supabase.py`, add a semaphore:

```python
import anyio
import asyncio
from supabase import create_client
from app.core.settings import settings

_client = create_client(settings.supabase_url, settings.supabase_key)
_TABLE = "games"

# Limit concurrent database operations
_semaphore = asyncio.Semaphore(5)  # Max 5 concurrent operations

async def search(query: str) -> list[dict[str, object]]:
    async with _semaphore:
        def _q():
            safe_query = query.replace('"', '\\"')
            term = f"*{safe_query}*"
            return _client.table(_TABLE).select("*").or_(f'title.ilike."{term}",description.ilike."{term}"').execute().data
        return await anyio.to_thread.run_sync(_q)

async def upsert(data: dict[str, object]) -> list[dict[str, object]]:
    async with _semaphore:
        def _q():
            # ... existing logic ...
        return await anyio.to_thread.run_sync(_q)

# Apply same pattern to get_by_id, get_by_slug, list_recent, increment_view_count
```

---

### Fix 3: Add Batch Processing with Rate Limiting

Create `app/services/batch_processor.py`:

```python
import asyncio
from typing import Callable, TypeVar, List
from app.core import logger

T = TypeVar("T")

async def batch_process(
    items: List[T],
    process_fn: Callable[[T], asyncio.coroutine],
    batch_size: int = 5,
    delay_between_batches: float = 0.5,
) -> List:
    """Process items in controlled batches with rate limiting."""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} items)")
        try:
            batch_results = await asyncio.gather(*[process_fn(item) for item in batch])
            results.extend(batch_results)
        except Exception as e:
            logger.error(f"Batch failed: {e}")
            raise
        if i + batch_size < len(items):
            await asyncio.sleep(delay_between_batches)
    return results
```

Usage in batch script:
```python
from app.services.batch_processor import batch_process
from app.services.game_service import GameService

async def update_batch_games():
    service = GameService()
    games_to_update = [...]  # List of slugs

    results = await batch_process(
        items=games_to_update,
        process_fn=lambda slug: service.update_game_content(slug),
        batch_size=5,
        delay_between_batches=0.5,
    )
    return results
```

---

### Fix 4: Add Retry Logic with Exponential Backoff

Create `app/utils/retry.py`:

```python
import asyncio
import random
from typing import Callable, TypeVar

T = TypeVar("T")

async def retry_with_backoff(
    fn: Callable,
    max_retries: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 10.0,
):
    """Retry with exponential backoff and jitter."""
    for attempt in range(max_retries):
        try:
            return await fn()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = min(initial_delay * (2 ** attempt) + random.random(), max_delay)
            await asyncio.sleep(delay)
```

Usage:
```python
from app.utils.retry import retry_with_backoff

async def safe_upsert(data):
    return await retry_with_backoff(
        fn=lambda: supabase.upsert(data),
        max_retries=3,
        initial_delay=1.0,
    )
```

---

## Monitoring Recommendations

### Add Metrics Logging

Update `app/core/supabase.py` to track operations:

```python
import time
from app.core import logger

async def search(query: str) -> list[dict[str, object]]:
    async with _semaphore:
        start = time.time()
        def _q():
            safe_query = query.replace('"', '\\"')
            term = f"*{safe_query}*"
            return _client.table(_TABLE).select("*").or_(f'title.ilike."{term}",description.ilike."{term}"').execute().data

        result = await anyio.to_thread.run_sync(_q)
        elapsed = time.time() - start
        logger.info(f"search({query[:20]}) took {elapsed:.2f}s, returned {len(result)} rows")
        return result
```

### Health Check Endpoint

Add to `app/routers/health.py` (or create if missing):

```python
from fastapi import APIRouter
from app.core import supabase

router = APIRouter()

@router.get("/health/db")
async def db_health():
    try:
        result = await supabase.list_recent(limit=1)
        return {"status": "healthy", "db_latency_ms": 0}  # Add actual latency tracking
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

## Implementation Plan

### Phase 1: Immediate (Emergency Fix)
1. Add semaphore to `app/core/supabase.py` (Fix 2)
2. Modify batch script to process games sequentially (batch_size=1) with 1-second delays
3. Add exception handling (don't silently catch)
4. Test with 10 games

### Phase 2: Short-term (Week 1)
1. Implement batch processor (Fix 3)
2. Add retry logic (Fix 4)
3. Add monitoring/metrics (logging)
4. Test with full 50+ game batch

### Phase 3: Medium-term (Week 2-3)
1. Implement connection pooling (Fix 1)
2. Configure pool sizes via `.env` (SUPABASE_POOL_SIZE, etc.)
3. Add health check endpoint
4. Document in CLAUDE.md

---

## Testing Checklist

- [ ] Script processes 50 games without timeout
- [ ] No "connection pool exceeded" errors in logs
- [ ] All games successfully updated (100% success rate)
- [ ] Script completes in <5 minutes for 50 games (~6 sec per game)
- [ ] Database remains responsive during batch processing
- [ ] Health check endpoint returns healthy status

---

## Environment Configuration

Add to `.env`:
```
SUPABASE_POOL_SIZE=5
SUPABASE_MAX_OVERFLOW=10
BATCH_PROCESSING_SIZE=5
BATCH_PROCESSING_DELAY=0.5
RETRY_MAX_ATTEMPTS=3
RETRY_INITIAL_DELAY=1.0
```

---

## References

- **Supabase SDK:** No built-in connection pooling; relies on underlying HTTP client
- **Python asyncio:** Thread pool size = CPU count + 4 (typically 8 on 4-core machine)
- **anyio.to_thread:** Creates new thread per call; not reused by default
- **Connection Pool Best Practices:** Max pool size = (CPU cores * 2) + 1 = 9 for 4-core system

---

## Gotchas & Known Issues

1. **Silent Exception Handling**: Current batch scripts swallow exceptions with bare `except`. This violates CDD principle and hides real errors. Fix: Let exceptions propagate with full traceback.

2. **Global Client Instance**: The Supabase client is a global singleton. Creating multiple instances in different threads can cause race conditions. Stick to single instance model.

3. **Async/Sync Boundary**: Using `anyio.to_thread.run_sync()` is correct for wrapping sync Supabase calls, but accumulates threads. Semaphore limits the damage.

4. **HTTP Timeout**: Supabase SDK default timeout may be too short for slow networks. If timeouts persist, consider increasing:
   ```python
   _client = create_client(
       settings.supabase_url,
       settings.supabase_key,
       timeout=30.0  # seconds
   )
   ```

---

## Quick Fix Script

If you need immediate relief, run this standalone:

```bash
#!/bin/bash
# scripts/batch_update_safe.sh

GAMES=("game-slug-1" "game-slug-2" "game-slug-3" ...)

for slug in "${GAMES[@]}"; do
    echo "Processing $slug..."
    python -c "
import asyncio
from app.services.game_service import GameService

async def main():
    svc = GameService()
    result = await svc.update_game_content('$slug')
    print(f'✅ {\"$slug\"} updated')

asyncio.run(main())
" || echo "❌ $slug failed"
    sleep 1  # 1-second delay between games
done
```

Run with: `bash scripts/batch_update_safe.sh`

This enforces sequential processing with explicit delays, avoiding pool exhaustion.

