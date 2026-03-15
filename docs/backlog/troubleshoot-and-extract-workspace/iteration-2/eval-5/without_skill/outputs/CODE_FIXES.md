# Code Fixes for Supabase Connection Pool Timeout

## Fix #1: Add Semaphore to Batch Processor (CRITICAL)

**File**: `app/core/supabase.py`
**Priority**: IMMEDIATE (Apply this first)

### Current Code (Lines 1-17):
```python
import anyio
from supabase import create_client

from app.core.settings import settings
from app.utils.slugify import slugify

_client = create_client(settings.supabase_url, settings.supabase_key)
_TABLE = "games"


async def search(query: str) -> list[dict[str, object]]:
    def _q():
        safe_query = query.replace('"', '\\"')
        term = f"*{safe_query}*"
        return _client.table(_TABLE).select("*").or_(f'title.ilike."{term}",description.ilike."{term}"').execute().data

    return await anyio.to_thread.run_sync(_q)
```

### Fixed Code:
```python
import anyio
import asyncio
from supabase import create_client

from app.core.settings import settings
from app.utils.slugify import slugify

_client = create_client(settings.supabase_url, settings.supabase_key)
_TABLE = "games"
_db_semaphore = asyncio.Semaphore(3)  # Max 3 concurrent DB operations


async def search(query: str) -> list[dict[str, object]]:
    async with _db_semaphore:
        def _q():
            safe_query = query.replace('"', '\\"')
            term = f"*{safe_query}*"
            return _client.table(_TABLE).select("*").or_(f'title.ilike."{term}",description.ilike."{term}"').execute().data

        return await anyio.to_thread.run_sync(_q)
```

### Why This Works:
- Semaphore limits concurrent asyncio tasks to 3, preventing unbounded thread creation
- Tasks queue in async context (non-blocking), not thread pool (blocking)
- Connection pool never exceeds 3 active connections

### Apply Semaphore to All DB Functions:
Apply same pattern to: `upsert()`, `get_by_id()`, `get_by_slug()`, `list_recent()`, `increment_view_count()`

Example for `upsert()`:
```python
async def upsert(data: dict[str, object]) -> list[dict[str, object]]:
    async with _db_semaphore:
        def _q():
            if data.get("title"):
                data["slug"] = slugify(str(data["title"]))
            for f in _URL_FIELDS:
                if data.get(f) == "":
                    data[f] = None
            if data.get("id"):
                key = "id"
            else:
                key = "source_url" if data.get("source_url") else "slug"
            return _client.table(_TABLE).upsert(data, on_conflict=key).execute().data

        return await anyio.to_thread.run_sync(_q)
```

---

## Fix #2: Add Timeout to Supabase Queries (HIGH PRIORITY)

**File**: `app/core/supabase.py`
**Priority**: HIGH (Apply after Fix #1)

### Current Problem:
Queries can hang indefinitely if Supabase is slow. No timeout protection.

### Solution: Wrap with asyncio timeout
```python
async def search(query: str, timeout_sec: int = 30) -> list[dict[str, object]]:
    async with _db_semaphore:
        try:
            async with asyncio.timeout(timeout_sec):
                def _q():
                    safe_query = query.replace('"', '\\"')
                    term = f"*{safe_query}*"
                    return _client.table(_TABLE).select("*").or_(f'title.ilike."{term}",description.ilike."{term}"').execute().data

                return await anyio.to_thread.run_sync(_q)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Supabase query exceeded {timeout_sec}s")
```

**Note**: `asyncio.timeout()` requires Python 3.11+ (already required by pyproject.toml).

### Apply to All Functions:
```python
async def upsert(data: dict[str, object], timeout_sec: int = 30) -> list[dict[str, object]]:
    async with _db_semaphore:
        try:
            async with asyncio.timeout(timeout_sec):
                def _q():
                    # ... existing code ...
                    return _client.table(_TABLE).upsert(data, on_conflict=key).execute().data

                return await anyio.to_thread.run_sync(_q)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Upsert exceeded {timeout_sec}s for slug: {data.get('slug')}")

async def get_by_slug(slug: str, timeout_sec: int = 30) -> dict[str, object] | None:
    async with _db_semaphore:
        try:
            async with asyncio.timeout(timeout_sec):
                def _q():
                    r = _client.table(_TABLE).select("*").eq("slug", slug).execute().data
                    return r[0] if r else None

                return await anyio.to_thread.run_sync(_q)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Get slug {slug} exceeded {timeout_sec}s")

async def list_recent(limit: int = 100, offset: int = 0, timeout_sec: int = 30) -> list[dict[str, object]]:
    async with _db_semaphore:
        try:
            async with asyncio.timeout(timeout_sec):
                def _q():
                    return (
                        _client.table(_TABLE)
                        .select("*")
                        .order("updated_at", desc=True)
                        .range(offset, offset + limit - 1)
                        .execute()
                        .data
                    )

                return await anyio.to_thread.run_sync(_q)
        except asyncio.TimeoutError:
            raise TimeoutError(f"List recent exceeded {timeout_sec}s (limit={limit}, offset={offset})")
```

---

## Fix #3: Update Batch Processor to Remove Retry Backoff

**File**: `troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/batch_processor.py`
**Priority**: MEDIUM (Keep backoff in Taskfile, not in app code)

### Problem with Current Code (Lines 77-133):
```python
async def batch_process_with_retry(...):
    for item in batch:
        success = False
        for attempt in range(1, max_retries + 1):
            try:
                result = await process_fn(item)
                ...
                success = True
                break
            except Exception as e:
                if attempt == max_retries:
                    logger.error(...)
                else:
                    wait_time = 2 ** attempt  # Exponential backoff - VIOLATES CDD
                    await asyncio.sleep(wait_time)
```

### Why It's Wrong:
- Per CDD rules: Retry logic belongs in **Taskfile/infra**, not app code
- Masks real errors behind sleeps (application appears "stuck")
- Exponential backoff leads to 2s + 4s + 8s = 14s latency per failed item

### Fixed Version:
```python
async def batch_process(
    items: List[T],
    process_fn: Callable[[T], Coroutine[Any, Any, R]],
    batch_size: int = 5,
    delay_between_batches: float = 2.0,
    on_error: str = "raise",  # "raise" or "skip"
) -> List[R]:
    """
    Process items in controlled batches with rate limiting.

    NO RETRY LOGIC: Let errors crash immediately.
    Retry at Taskfile level with exponential backoff.
    """
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(items), batch_size):
        batch_num = batch_idx // batch_size + 1
        batch = items[batch_idx : batch_idx + batch_size]

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")

        try:
            batch_results = await asyncio.gather(
                *[process_fn(item) for item in batch],
                return_exceptions=on_error == "skip",
            )

            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    if on_error == "raise":
                        raise result
                    elif on_error == "skip":
                        logger.warning(f"Skipped item {batch[i]}: {result}")
                else:
                    results.append(result)

        except Exception as e:
            logger.error(f"Batch {batch_num} failed: {e}")
            if on_error == "raise":
                raise
            else:
                continue

        if batch_idx + batch_size < len(items):
            logger.info(f"Waiting {delay_between_batches}s before next batch...")
            await asyncio.sleep(delay_between_batches)

    logger.info(f"Batch processing complete: {len(results)}/{len(items)} items")
    return results
```

### Changes:
1. **Removed**: `batch_process_with_retry()` function entirely
2. **Removed**: Exponential backoff loop
3. **Added**: `delay_between_batches` increased from 0.5s → 2.0s
4. **Changed**: On error, either raise immediately or skip (no retry)

### Taskfile-Level Retry (NEW):
Add to `Taskfile.yml`:
```yaml
tasks:
  batch:extract-pdf:
    desc: "Extract PDF rules for 50+ games with auto-retry"
    cmds:
      - until python scripts/batch_pdf_extract.py; do echo "Retrying in 10s..." && sleep 10; done
    # Retries up to 3 times with 10s backoff between runs

  batch:extract-pdf-fast:
    desc: "Extract 50 games without retry (fail fast)"
    cmds:
      - python scripts/batch_pdf_extract.py
```

---

## Fix #4: Increase Delay Between Batches

**File**: Batch script (wherever you call `batch_process`)
**Priority**: LOW (Works in combination with Fixes 1-3)

### Before:
```python
results = await batch_process(games, process_fn, batch_size=5, delay_between_batches=0.5)
```

### After:
```python
results = await batch_process(games, process_fn, batch_size=5, delay_between_batches=2.0)
```

### Why:
- 0.5s: Next batch starts before previous batch connections close
- 2.0s: Gives 2s for thread cleanup + connection return to pool
- Combined with semaphore (Fix #1), prevents pool starvation

---

## Fix #5: Add Connection Pool Warmup (OPTIONAL)

**File**: `app/core/supabase.py` (at module initialization)
**Priority**: LOW (Nice-to-have for performance)

### Add After `_client` Creation (Line 7):
```python
async def _warmup_pool():
    """Warmup Supabase connection pool on startup."""
    try:
        async with _db_semaphore:
            def _q():
                return _client.table(_TABLE).select("id").limit(1).execute().data
            await anyio.to_thread.run_sync(_q)
        logger.info("✅ Supabase connection pool warmed up")
    except Exception as e:
        logger.warning(f"⚠️ Warmup failed (non-fatal): {e}")

# Call during FastAPI startup:
# In app/main.py:
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await supabase._warmup_pool()
    yield

app = FastAPI(lifespan=lifespan)
```

### Why:
- First query after cold start is slow (~1-2s)
- Warmup "primes" connection; subsequent queries faster
- Optional: Not critical, just improves user experience

---

## Summary: Apply in Order

| Order | Fix | File | Impact |
|-------|-----|------|--------|
| 1 | Semaphore limit (3 concurrent) | `app/core/supabase.py` | Prevents thread pool exhaustion |
| 2 | Timeout on all queries (30s) | `app/core/supabase.py` | Prevents indefinite hangs |
| 3 | Remove retry backoff, increase delay to 2s | `batch_processor.py` / batch script | Allows pool recovery between batches |
| 4 | Update Taskfile with retry logic | `Taskfile.yml` | Move resilience to infra |
| 5 | Optional: Warmup on startup | `app/main.py` | Slight perf improvement |

---

## Validation Checklist

After applying fixes:

- [ ] `uv run ruff check .` passes (no lint errors)
- [ ] Import `asyncio` in `supabase.py` succeeds
- [ ] Semaphore limit set to 3 (test with `assert _db_semaphore._value == 3`)
- [ ] Timeout wrapped around all `anyio.to_thread.run_sync()` calls
- [ ] `batch_process_with_retry()` removed from batch_processor.py
- [ ] Delay increased to 2.0s in batch function calls
- [ ] Run test batch with 20 games → completes without timeouts
- [ ] Run test batch with 50 games → completes in <5 min
- [ ] Monitor max concurrent threads during 50-game run → never exceeds 7

