# Implementation Steps: Database Connection Pool Fix

## Overview

This document outlines the exact steps to implement the connection pool exhaustion fixes for the rule-scribe-games batch PDF extraction pipeline.

---

## Phase 1: Emergency Fix (Immediate, 10 minutes)

Use this if you need to process games right now without rewriting code.

### Step 1.1: Use the Safe Shell Script

```bash
cd /home/kafka/projects/rule-scribe-games

# Make the script executable
chmod +x troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/batch_update_safe.sh

# Copy to scripts directory
cp troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/batch_update_safe.sh scripts/

# Run the safe batch updater
bash scripts/batch_update_safe.sh
```

**What it does:**
- Processes games **sequentially** (one at a time)
- Adds **1-second delay** between games
- Prevents connection pool exhaustion
- Logs success/failure clearly

**Expected result:** All 50 games processed in ~50-60 seconds without timeouts.

---

## Phase 2: Short-term Fix (30 minutes, Week 1)

Implement semaphore-based concurrency control.

### Step 2.1: Backup Current Supabase Module

```bash
cp app/core/supabase.py app/core/supabase.py.backup
```

### Step 2.2: Apply Semaphore Fix

Replace `app/core/supabase.py` with the semaphore version:

```bash
cp troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/supabase_with_semaphore.py app/core/supabase.py
```

**What changed:**
- Added `asyncio.Semaphore(5)` to limit concurrent operations
- All database calls acquire the semaphore before executing
- Max 5 concurrent Supabase operations instead of unlimited

**Verification:**
```bash
# Start the backend
task dev:backend

# In another terminal, test with a small batch
python -c "
import asyncio
from app.services.game_service import GameService

async def test():
    svc = GameService()
    for i in range(10):
        result = await svc.search_games(f'test-{i}')
        print(f'Query {i} returned {len(result)} results')

asyncio.run(test())
"
```

---

### Step 2.3: Add Batch Processor Module

```bash
cp troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/batch_processor.py app/services/

cp troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/retry.py app/utils/
```

### Step 2.4: Update Your Batch Script

If you have a custom batch script, convert it to use the batch processor.

**Before (hangs on game 20):**
```python
import asyncio
from app.core import supabase

async def main():
    games = ["game1", "game2", ..., "game50"]
    for game in games:
        await supabase.upsert({"slug": game, "title": game})
```

**After (handles all 50):**
```python
import asyncio
from app.services.batch_processor import batch_process
from app.services.game_service import GameService

async def main():
    svc = GameService()
    games = ["game1", "game2", ..., "game50"]

    results = await batch_process(
        items=games,
        process_fn=lambda slug: svc.update_game_content(slug),
        batch_size=5,
        delay_between_batches=0.5,
        on_error="raise",
    )
    print(f"Updated {len(results)} games")

asyncio.run(main())
```

### Step 2.5: Test the Batch Processor

```bash
# Test with 20 games (should take ~10 seconds)
python scripts/your_batch_script.py
```

**Expected logs:**
```
Processing batch 1/4 (5 items)
✅ game1 updated
✅ game2 updated
✅ game3 updated
✅ game4 updated
✅ game5 updated
Waiting 0.5s before next batch...
Processing batch 2/4 (5 items)
...
Batch processing complete: 20/20 items
```

---

## Phase 3: Medium-term Fix (1-2 hours, Week 1-2)

Add connection pooling and monitoring.

### Step 3.1: Add Pool Configuration Module

```bash
cp troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/supabase_pool.py app/core/
```

### Step 3.2: Update `.env` for Pool Sizing

Add to `.env`:
```env
SUPABASE_POOL_SIZE=5
SUPABASE_MAX_OVERFLOW=10
BATCH_PROCESSING_SIZE=5
BATCH_PROCESSING_DELAY=0.5
RETRY_MAX_ATTEMPTS=3
RETRY_INITIAL_DELAY=1.0
```

### Step 3.3: Add Health Check Endpoint

Create `app/routers/health.py`:

```python
from fastapi import APIRouter
from app.core import supabase

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/db")
async def db_health():
    try:
        result = await supabase.list_recent(limit=1)
        return {"status": "healthy", "records": len(result)}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503
```

Add to `app/main.py`:
```python
from app.routers import health

app.include_router(health.router)
```

### Step 3.4: Add Monitoring to Game Service

Create `app/utils/metrics.py`:

```python
import time
from app.core import logger

class Metrics:
    def __init__(self):
        self.operations = []

    def record(self, operation: str, duration: float, status: str = "success"):
        self.operations.append({
            "operation": operation,
            "duration": duration,
            "status": status,
        })
        if duration > 5.0:
            logger.warning(f"Slow operation: {operation} took {duration:.2f}s")

metrics = Metrics()
```

Update `app/core/supabase.py` to log operation timing:

```python
import time

async def upsert(data: dict[str, object]) -> list[dict[str, object]]:
    async with _semaphore:
        start = time.time()
        def _q():
            # ... existing logic ...
        result = await anyio.to_thread.run_sync(_q)
        elapsed = time.time() - start
        from app.utils.metrics import metrics
        metrics.record("upsert", elapsed)
        return result
```

### Step 3.5: Test End-to-End

```bash
# Start backend with monitoring
task dev:backend

# In another terminal, run full batch
python scripts/your_batch_script.py 2>&1 | tee batch.log

# Check health
curl http://localhost:8000/health/db | jq

# Review logs for slow operations
grep "Slow operation" batch.log
```

---

## Phase 4: Validation & Testing

Run these checks after each phase:

### Check 1: No Connection Pool Errors

```bash
grep -i "connection pool" batch.log
grep -i "connection exceeded" batch.log
grep -i "timeout" batch.log
```

If any matches: connection pool still exhausted. Go back to Phase 2.

### Check 2: 100% Success Rate

```bash
grep "updated successfully" batch.log | wc -l
# Should equal total games

grep "failed:" batch.log | wc -l
# Should be 0
```

### Check 3: Performance Target

```bash
# Time the full batch (should be <5 min for 50 games = ~6 sec/game)
time python scripts/your_batch_script.py
```

### Check 4: Database Remains Responsive

```bash
# While batch is running in one terminal, test responsiveness in another
watch -n 1 "curl -s http://localhost:8000/api/games/catan | jq '.id' && echo OK"
```

Should see results every second, not stalled.

---

## Rollback Plan

If something breaks:

```bash
# Restore original supabase.py
cp app/core/supabase.py.backup app/core/supabase.py

# Remove new modules
rm -f app/services/batch_processor.py
rm -f app/utils/retry.py
rm -f app/core/supabase_pool.py

# Restart backend
task kill
task dev:backend
```

---

## Troubleshooting During Implementation

### Issue: "asyncio.Semaphore not found"

**Cause:** Python version too old or asyncio import missing.

**Fix:**
```python
import asyncio  # Add this to app/core/supabase.py if missing
```

### Issue: "batch_process function not found"

**Cause:** Module not copied correctly.

**Fix:**
```bash
ls -la app/services/batch_processor.py  # Check it exists
python -c "from app.services.batch_processor import batch_process; print('OK')"
```

### Issue: Script still hangs after Phase 2

**Cause:** Semaphore limit too high, or other scripts bypassing it.

**Fix:**
```bash
# Lower semaphore limit
# In app/core/supabase.py, change:
_semaphore = asyncio.Semaphore(3)  # Instead of 5
```

### Issue: "slowdown, not faster" after changes

**Cause:** Semaphore is too restrictive (limit too low).

**Fix:**
```bash
# Increase semaphore and batch size
# In app/core/supabase.py:
_semaphore = asyncio.Semaphore(10)  # Increase limit

# In batch_process calls:
batch_size=10,  # Increase batch size
```

Tune based on monitoring data (see Phase 3.4).

---

## Quick Checklist

- [ ] Phase 1: Emergency fix script works for 10 games
- [ ] Phase 1: No timeout errors in logs
- [ ] Phase 2: Semaphore applied to supabase.py
- [ ] Phase 2: Batch processor and retry modules added
- [ ] Phase 2: Batch script updated to use new modules
- [ ] Phase 2: Full 50-game batch completes without errors
- [ ] Phase 3: Pool config and health check added
- [ ] Phase 3: Monitoring metrics in place
- [ ] Phase 3: Health check endpoint returns "healthy"
- [ ] Validation: No connection pool errors in logs
- [ ] Validation: 100% success rate
- [ ] Validation: <5 minutes for 50 games
- [ ] Validation: Database responsive during batch

---

## Production Readiness

Once all phases complete:

1. **Commit changes:**
   ```bash
   git add app/core/supabase.py app/services/batch_processor.py app/utils/retry.py
   git commit -m "fix(db): add connection pool limiting and batch processing"
   ```

2. **Update CLAUDE.md:**
   Add section under "Batch Processing":
   ```markdown
   ## Batch Processing Pattern

   For safe batch updates (50+ items):
   ```python
   from app.services.batch_processor import batch_process
   results = await batch_process(
       items=games,
       process_fn=lambda game: service.update(game),
       batch_size=5,
       delay_between_batches=0.5,
   )
   ```
   ```

3. **Monitor in production:**
   - Check `/health/db` endpoint regularly
   - Alert if response time > 1 second
   - Track batch processing metrics in logs

---

## Questions?

Refer to:
- `database-infrastructure-diagnostic.md` — Root cause analysis and gotchas
- `supabase_with_semaphore.py` — Detailed code comments
- `batch_processor.py` — API documentation
