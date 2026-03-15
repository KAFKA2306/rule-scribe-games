# Quick Reference: Supabase Connection Pool Fix

## Problem
Batch PDF extraction hangs around game 15-20 with "connection pool exceeded" error when processing 50+ games.

## Root Cause
Single synchronous Supabase client shared across unbounded concurrent threads → all 10 connections claimed by game 15 → remaining threads queue indefinitely.

## The Fix (In Order)

### Step 1: Add Semaphore to Limit Concurrency (CRITICAL)
**File**: `app/core/supabase.py`

**Add at top**:
```python
import asyncio
_db_semaphore = asyncio.Semaphore(3)
```

**Wrap each async function**:
```python
async def search(query: str) -> list[dict[str, object]]:
    async with _db_semaphore:
        def _q():
            # ... existing code ...
        return await anyio.to_thread.run_sync(_q)
```

**Time to fix**: 5 minutes (7 functions)

---

### Step 2: Add Timeout to Queries (HIGH PRIORITY)
**File**: `app/core/supabase.py`

**Wrap each function with timeout**:
```python
async def search(query: str) -> list[dict[str, object]]:
    async with _db_semaphore:
        try:
            async with asyncio.timeout(30):
                def _q():
                    # ... existing code ...
                return await anyio.to_thread.run_sync(_q)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Search query exceeded 30s")
```

**Time to fix**: 3 minutes per function

---

### Step 3: Increase Batch Delay
**File**: Batch processing script (wherever you call batch_process)

**Change**:
```python
# OLD:
results = await batch_process(games, process_fn, delay_between_batches=0.5)

# NEW:
results = await batch_process(games, process_fn, delay_between_batches=2.0)
```

**Time to fix**: 1 minute

---

### Step 4: Remove Retry Backoff (Move to Taskfile)
**File**: `batch_processor.py`

**Remove**: `batch_process_with_retry()` function entirely (it violates CDD rules)

**Add to Taskfile.yml**:
```yaml
batch:extract-pdf:
  desc: "Extract PDF rules with auto-retry"
  cmds:
    - until python scripts/batch_pdf_extract.py; do echo "Retrying..." && sleep 10; done
```

**Time to fix**: 2 minutes

---

## Expected Results

| Metric | Before | After |
|--------|--------|-------|
| Games processed | 15-20 (hangs) | 50 (complete) |
| Concurrent threads | 15-20+ (unbounded) | 10-15 (capped) |
| Connection pool usage | 10/10 (exhausted) | 3-5/10 (normal) |
| Time per game | N/A (hangs) | 0.45s (steady) |
| Total 50-game time | Timeout (~300s) | 115s (complete) |

---

## Testing

### Quick Test: 5 games (30 seconds)
```bash
python scripts/test_small_batch.py
```
Expected: All 5 complete in <60s, each <1.5s

### Full Test: 50 games (2 minutes)
```bash
python scripts/test_large_batch.py
```
Expected: All 50 complete in <300s, each <0.8s, max 18 threads

---

## Monitoring During Run

**Terminal 1**: Run batch
```bash
python scripts/batch_pdf_extract.py 2>&1 | tee batch.log
```

**Terminal 2**: Watch threads
```bash
watch -n2 "ps aux | grep python | wc -l"
```

**Terminal 3**: Tail errors
```bash
tail -f batch.log | grep -E "(ERROR|timeout|connection)"
```

---

## Rollback (If Something Breaks)

```bash
# If tests fail after Fix #1-2:
git diff app/core/supabase.py  # Review changes
git checkout app/core/supabase.py  # Undo

# If timeout 30s is too short:
# Change to 60s in supabase.py:
async with asyncio.timeout(60):  # Increase from 30

# If semaphore 3 is too restrictive:
# Change in supabase.py:
_db_semaphore = asyncio.Semaphore(5)  # Increase from 3
```

---

## Files Modified

| File | Change | Priority |
|------|--------|----------|
| `app/core/supabase.py` | Add semaphore + timeout | **CRITICAL** |
| `batch_processor.py` | Remove retry backoff | HIGH |
| Batch script | Increase delay to 2.0s | MEDIUM |
| `Taskfile.yml` | Add batch:extract-pdf task | MEDIUM |

---

## Common Issues & Solutions

### "Still timing out after Fix #1"
**Diagnosis**: Semaphore limit too high OR timeout too short
```python
# Lower semaphore limit:
_db_semaphore = asyncio.Semaphore(2)  # Was 3

# OR increase timeout:
async with asyncio.timeout(60):  # Was 30
```

### "Batch slower than expected (>1.0s/game)"
**Diagnosis**: Supabase database degraded OR network latency
```bash
# Check Supabase status:
curl -s https://status.supabase.com/api/v2/summary.json | jq .status.indicator

# Test baseline latency:
time curl -H "apikey: $SUPABASE_KEY" \
  https://<project>.supabase.co/rest/v1/games?limit=1
```

### "Script completes but only processed 30/50 games"
**Diagnosis**: on_error="skip" is silently dropping failures
```python
# Change in batch_process call:
results = await batch_process(games, fn, on_error="raise")  # Was "skip"
```

---

## Performance Tuning (Optional)

### For Slower Networks (>200ms latency)
```python
# In supabase.py:
_db_semaphore = asyncio.Semaphore(2)  # Lower from 3
async with asyncio.timeout(60):  # Increase from 30
```

### For Faster Networks (<50ms latency)
```python
# In supabase.py:
_db_semaphore = asyncio.Semaphore(5)  # Increase from 3
async with asyncio.timeout(20):  # Decrease from 30

# In batch script:
delay_between_batches=1.0  # Decrease from 2.0
```

### For Large Batches (100+ games)
```python
# In batch script:
batch_size=10  # Increase from 5 (more items per batch)
delay_between_batches=3.0  # Increase from 2.0 (more recovery time)
```

---

## Validation Checklist

- [ ] Added `import asyncio` to `supabase.py`
- [ ] Created `_db_semaphore = asyncio.Semaphore(3)` at module level
- [ ] Wrapped all async functions with `async with _db_semaphore:`
- [ ] Added `asyncio.timeout(30)` to all `anyio.to_thread.run_sync()` calls
- [ ] Changed batch delay from 0.5s → 2.0s
- [ ] Removed `batch_process_with_retry()` function
- [ ] Added batch task to Taskfile with retry logic
- [ ] Ran `python scripts/test_small_batch.py` → passed
- [ ] Ran `python scripts/test_large_batch.py` → passed
- [ ] Ran `uv run ruff check .` → no errors

---

## Key Insights

1. **Semaphore is the cure**: Limits concurrent DB operations to queue in async context, not thread pool
2. **Timeout prevents ghosts**: Forces errors to surface instead of hanging indefinitely
3. **Delay allows recovery**: 2s between batches lets thread pool cool down and connections return
4. **Retry in infra, not app**: CDD principle—application crashes fast, infrastructure retries
5. **Thread count reveals pool**: If max threads > 20, semaphore limit too high

---

## References

- **Diagnostic**: See `DIAGNOSTIC_ANALYSIS.md`
- **Code Changes**: See `CODE_FIXES.md`
- **Monitoring**: See `MONITORING_SETUP.md`
- **Testing**: See `TESTING_GUIDE.md`

