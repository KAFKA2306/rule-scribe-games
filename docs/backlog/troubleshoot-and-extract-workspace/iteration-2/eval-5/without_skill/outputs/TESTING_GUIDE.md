# Testing & Validation Guide for Connection Pool Fix

## Pre-Fix Verification (Reproduce the Problem)

### Test 1: Baseline - Confirm Pool Exhaustion
**Purpose**: Verify the problem exists before applying fixes.

**Prerequisites**:
- Ensure `.env` has valid `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Ensure database has at least 20 games

**Script** (`scripts/test_pool_exhaustion.py`):
```python
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.core import supabase
from app.core.logger import setup_logging

setup_logging()

async def stress_test():
    """Send 20 concurrent DB queries to force pool exhaustion."""
    print("Starting pool exhaustion test...")
    print("Expected: Timeout after 15-20 games OR hangs indefinitely")

    games = [
        {"title": f"Test Game {i}", "slug": f"test-game-{i}", "summary": f"Summary {i}"}
        for i in range(20)
    ]

    try:
        tasks = [supabase.upsert(game) for game in games]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        errors = [r for r in results if isinstance(r, Exception)]
        print(f"\n{'='*50}")
        print(f"Results: {len(results) - len(errors)} succeeded, {len(errors)} failed")
        if errors:
            print(f"First error: {errors[0]}")
        print(f"{'='*50}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    timeout_sec = 120
    try:
        asyncio.run(asyncio.wait_for(stress_test(), timeout=timeout_sec))
    except asyncio.TimeoutError:
        print(f"❌ Test timed out after {timeout_sec}s - POOL EXHAUSTION CONFIRMED")
        sys.exit(1)
```

**Run**:
```bash
python scripts/test_pool_exhaustion.py
```

**Expected Output (BEFORE FIX)**:
```
Starting pool exhaustion test...
Expected: Timeout after 15-20 games OR hangs indefinitely
...
❌ Test timed out after 120s - POOL EXHAUSTION CONFIRMED
```

**If you see this**: Problem confirmed; proceed with Fix #1.

---

## Post-Fix Validation

### Test 2: Small Batch (5 Games)
**Purpose**: Verify Fix #1 (semaphore) prevents pool exhaustion on small scale.

**Script** (`scripts/test_small_batch.py`):
```python
import asyncio
import sys
import os
import time

sys.path.append(os.getcwd())

from app.core import supabase
from app.core.logger import setup_logging

setup_logging()

async def test_small_batch():
    """Process 5 games sequentially and verify no hangs."""
    print("Test 2: Small batch (5 games)")
    print("-" * 50)

    games = [
        {"title": f"Small Batch Game {i}", "slug": f"small-{i}", "summary": f"Batch test {i}"}
        for i in range(5)
    ]

    results = []
    for i, game in enumerate(games, 1):
        start = time.time()
        try:
            result = await supabase.upsert(game)
            elapsed = time.time() - start
            print(f"✅ Game {i}: {elapsed:.2f}s")
            results.append(result)
        except Exception as e:
            elapsed = time.time() - start
            print(f"❌ Game {i}: {e} ({elapsed:.2f}s)")
            results.append(None)

    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(asyncio.wait_for(test_small_batch(), timeout=60))
        success_count = sum(1 for r in results if r)
        print(f"\n{'='*50}")
        print(f"✅ PASSED: {success_count}/5 games completed in <60s")
        print(f"{'='*50}")
    except asyncio.TimeoutError:
        print(f"\n❌ FAILED: Test timed out - semaphore fix not working")
        sys.exit(1)
```

**Run**:
```bash
python scripts/test_small_batch.py
```

**Expected Output (AFTER FIX)**:
```
Test 2: Small batch (5 games)
--------------------------------------------------
✅ Game 1: 0.45s
✅ Game 2: 0.42s
✅ Game 3: 0.51s
✅ Game 4: 0.48s
✅ Game 5: 0.43s

==================================================
✅ PASSED: 5/5 games completed in <60s
==================================================
```

**Pass Criteria**:
- [ ] All 5 games complete
- [ ] Total time < 60 seconds
- [ ] Each game < 1.5 seconds (indicates no pool contention)

---

### Test 3: Medium Batch (20 Games)
**Purpose**: Verify Fix #2 (timeout) prevents indefinite hangs.

**Script** (`scripts/test_medium_batch.py`):
```python
import asyncio
import sys
import os
import time

sys.path.append(os.getcwd())

from app.core import supabase
from app.core.logger import setup_logging

setup_logging()

async def process_game(game):
    """Simulate game processing."""
    start = time.time()
    try:
        result = await supabase.upsert(game)
        elapsed = time.time() - start
        return {"title": game["title"], "elapsed": elapsed, "success": True}
    except Exception as e:
        elapsed = time.time() - start
        return {"title": game["title"], "elapsed": elapsed, "success": False, "error": str(e)}

async def test_medium_batch():
    """Process 20 games with controlled concurrency."""
    print("Test 3: Medium batch (20 games)")
    print("-" * 50)

    games = [
        {"title": f"Medium Batch Game {i}", "slug": f"medium-{i}", "summary": f"Batch {i}"}
        for i in range(20)
    ]

    # Simulate 4 concurrent tasks (matches semaphore in Fix #1)
    batch_size = 5
    all_results = []

    for batch_idx in range(0, len(games), batch_size):
        batch = games[batch_idx : batch_idx + batch_size]
        print(f"\nBatch {batch_idx // batch_size + 1}/4:")

        tasks = [process_game(game) for game in batch]
        batch_results = await asyncio.gather(*tasks)

        for result in batch_results:
            all_results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['title']}: {result['elapsed']:.2f}s")

        if batch_idx + batch_size < len(games):
            print("  Waiting 2s before next batch...")
            await asyncio.sleep(2.0)

    return all_results

if __name__ == "__main__":
    start_time = time.time()
    try:
        results = asyncio.run(asyncio.wait_for(test_medium_batch(), timeout=300))
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r["success"])

        avg_time = sum(r["elapsed"] for r in results) / len(results)
        max_time = max(r["elapsed"] for r in results)

        print(f"\n{'='*50}")
        print(f"✅ PASSED: {success_count}/20 games completed")
        print(f"Total time: {total_time:.1f}s (target: <180s)")
        print(f"Avg time/game: {avg_time:.2f}s")
        print(f"Max time/game: {max_time:.2f}s")
        print(f"{'='*50}")

        if success_count == 20 and total_time < 180:
            print("✅ All validation criteria met")
        else:
            print("⚠️ Some criteria not met")
            sys.exit(1)

    except asyncio.TimeoutError:
        print(f"\n❌ FAILED: Test timed out after 5 minutes")
        print("Check: Is timeout fix applied? Semaphore working?")
        sys.exit(1)
```

**Run**:
```bash
python scripts/test_medium_batch.py
```

**Expected Output (AFTER FIX)**:
```
Test 3: Medium batch (20 games)
--------------------------------------------------

Batch 1/4:
  ✅ Medium Batch Game 0: 0.48s
  ✅ Medium Batch Game 1: 0.45s
  ✅ Medium Batch Game 2: 0.47s
  ✅ Medium Batch Game 3: 0.50s
  ✅ Medium Batch Game 4: 0.44s
  Waiting 2s before next batch...

Batch 2/4:
  ✅ Medium Batch Game 5: 0.46s
...

==================================================
✅ PASSED: 20/20 games completed
Total time: 45.2s (target: <180s)
Avg time/game: 0.45s
Max time/game: 0.52s
==================================================
✅ All validation criteria met
```

**Pass Criteria**:
- [ ] 20/20 games complete
- [ ] Total time < 180 seconds (3 minutes)
- [ ] Max time/game < 1.0 second
- [ ] No timeout errors

---

### Test 4: Large Batch Stress Test (50 Games)
**Purpose**: Verify full fix prevents pool exhaustion at scale.

**Script** (`scripts/test_large_batch.py`):
```python
import asyncio
import sys
import os
import time
import json
from datetime import datetime

sys.path.append(os.getcwd())

from app.core import supabase
from app.core.logger import setup_logging
import threading

setup_logging()

async def process_game(game, index):
    """Process a single game with timing."""
    start = time.time()
    try:
        # Simulate real work: search then upsert
        await supabase.search(game["title"])
        result = await supabase.upsert(game)
        elapsed = time.time() - start
        return {
            "index": index,
            "title": game["title"],
            "elapsed": elapsed,
            "success": True,
            "threads": threading.active_count(),
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "index": index,
            "title": game["title"],
            "elapsed": elapsed,
            "success": False,
            "error": str(e),
            "threads": threading.active_count(),
        }

async def test_large_batch():
    """Process 50 games in batches of 5."""
    print("Test 4: Large batch (50 games)")
    print("-" * 50)
    print(f"Start time: {datetime.now().isoformat()}")

    games = [
        {"title": f"Large Batch Game {i}", "slug": f"large-{i}", "summary": f"Stress test {i}"}
        for i in range(50)
    ]

    batch_size = 5
    all_results = []
    max_threads = 0

    for batch_idx in range(0, len(games), batch_size):
        batch_num = batch_idx // batch_size + 1
        batch = games[batch_idx : batch_idx + batch_size]
        print(f"\nBatch {batch_num}/10: Processing games {batch_idx + 1}-{batch_idx + len(batch)}")

        # Start all tasks in parallel
        tasks = [process_game(game, batch_idx + i) for i, game in enumerate(batch)]
        batch_results = await asyncio.gather(*tasks)

        for result in batch_results:
            all_results.append(result)
            max_threads = max(max_threads, result.get("threads", 0))
            status = "✅" if result["success"] else "❌"
            print(f"  {status} [{result['index']+1:2d}] {result['title']}: {result['elapsed']:.2f}s (threads: {result['threads']})")

        if batch_idx + batch_size < len(games):
            print(f"  Waiting 2s before batch {batch_num + 1}...")
            await asyncio.sleep(2.0)

    return all_results, max_threads

if __name__ == "__main__":
    start_time = time.time()
    try:
        results, max_threads = asyncio.run(asyncio.wait_for(test_large_batch(), timeout=600))
        total_time = time.time() - start_time

        success_count = sum(1 for r in results if r["success"])
        failed = [r for r in results if not r["success"]]

        timings = [r["elapsed"] for r in results if r["success"]]
        avg_time = sum(timings) / len(timings) if timings else 0
        max_time = max(timings) if timings else 0

        print(f"\n{'='*60}")
        print(f"RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Total games: 50")
        print(f"Successful: {success_count}/50 ({success_count*100//50}%)")
        print(f"Failed: {len(failed)}/50")
        print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
        print(f"Avg time/game: {avg_time:.2f}s")
        print(f"Max time/game: {max_time:.2f}s")
        print(f"Max concurrent threads: {max_threads}")
        print(f"{'='*60}")

        # Validation
        checks = [
            ("All games completed", success_count == 50),
            ("Total time < 5 min", total_time < 300),
            ("Avg time < 0.8s/game", avg_time < 0.8),
            ("Max threads < 25", max_threads < 25),
            ("No timeouts", not any("timeout" in str(r.get("error", "")).lower() for r in failed)),
        ]

        for check_name, passed in checks:
            symbol = "✅" if passed else "❌"
            print(f"{symbol} {check_name}")

        all_passed = all(p for _, p in checks)
        print(f"{'='*60}")
        if all_passed:
            print("✅ ALL CHECKS PASSED - Fix is working!")
            sys.exit(0)
        else:
            print("❌ SOME CHECKS FAILED - Review results above")
            if failed:
                print("\nFailed games:")
                for r in failed[:5]:
                    print(f"  - {r['title']}: {r.get('error', 'Unknown error')}")
            sys.exit(1)

    except asyncio.TimeoutError:
        print(f"\n❌ FAILED: Test timed out after 10 minutes")
        print("Likely causes:")
        print("  - Semaphore limit not applied correctly")
        print("  - Connection pool limit still too high")
        print("  - Supabase database degraded")
        sys.exit(1)
```

**Run**:
```bash
python scripts/test_large_batch.py
```

**Expected Output (AFTER ALL FIXES)**:
```
Test 4: Large batch (50 games)
--------------------------------------------------
Start time: 2026-03-15T10:30:00.123456

Batch 1/10: Processing games 1-5
  ✅ [ 1] Large Batch Game 0: 0.48s (threads: 12)
  ✅ [ 2] Large Batch Game 1: 0.45s (threads: 12)
  ✅ [ 3] Large Batch Game 2: 0.51s (threads: 13)
  ✅ [ 4] Large Batch Game 3: 0.47s (threads: 13)
  ✅ [ 5] Large Batch Game 4: 0.44s (threads: 12)
  Waiting 2s before batch 2...

Batch 2/10: Processing games 6-10
...

============================================================
RESULTS SUMMARY
============================================================
Total games: 50
Successful: 50/50 (100%)
Failed: 0/50
Total time: 115.3s (1.9 min)
Avg time/game: 0.45s
Max time/game: 0.82s
Max concurrent threads: 18
============================================================
✅ All games completed
✅ Total time < 5 min
✅ Avg time < 0.8s/game
✅ Max threads < 25
✅ No timeouts
============================================================
✅ ALL CHECKS PASSED - Fix is working!
```

**Pass Criteria**:
- [ ] 50/50 games complete (100%)
- [ ] Total time < 5 minutes
- [ ] Avg time/game < 0.8 seconds
- [ ] Max threads < 25
- [ ] No timeout errors

---

## Regression Testing (After Any Code Changes)

### Test 5: API Endpoint Integration Test
**Purpose**: Verify fixes don't break existing FastAPI endpoints.

**Script** (`scripts/test_api_integration.py`):
```python
import subprocess
import sys
import time
import requests
import asyncio

async def test_api():
    """Test critical API endpoints."""
    print("Test 5: API Integration")
    print("-" * 50)

    # Start dev server
    print("Starting FastAPI server...")
    server = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    time.sleep(3)  # Wait for server startup

    try:
        base_url = "http://127.0.0.1:8000"

        # Test 1: Search
        print("Testing GET /api/search...")
        response = requests.get(f"{base_url}/api/search", params={"q": "test"})
        assert response.status_code == 200, f"Search failed: {response.status_code}"
        print("✅ Search OK")

        # Test 2: List
        print("Testing GET /api/games...")
        response = requests.get(f"{base_url}/api/games")
        assert response.status_code == 200, f"List failed: {response.status_code}"
        print("✅ List OK")

        # Test 3: Detail (use first game slug from list)
        games = response.json().get("games", [])
        if games:
            slug = games[0].get("slug")
            print(f"Testing GET /api/games/{slug}...")
            response = requests.get(f"{base_url}/api/games/{slug}")
            assert response.status_code == 200, f"Detail failed: {response.status_code}"
            print("✅ Detail OK")

        print("\n" + "="*50)
        print("✅ All API endpoints working")
        print("="*50)
        return True

    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

    finally:
        server.terminate()
        server.wait(timeout=5)

if __name__ == "__main__":
    try:
        success = asyncio.run(test_api())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test error: {e}")
        sys.exit(1)
```

**Run**:
```bash
python scripts/test_api_integration.py
```

---

## Cleanup After Testing

```bash
# Remove test games from database (optional)
# Run in Supabase SQL Editor:
DELETE FROM games WHERE slug LIKE 'test-%' OR slug LIKE 'small-%' OR slug LIKE 'medium-%' OR slug LIKE 'large-%';

# Clean up test scripts
rm scripts/test_*.py

# Archive test logs
mkdir -p test_results/$(date +%Y%m%d)
mv batch_*.log test_results/$(date +%Y%m%d)/ 2>/dev/null || true
```

---

## Testing Summary

| Test | Games | Time Target | Passes When |
|------|-------|-------------|------------|
| Pool Exhaustion (baseline) | 20 | 120s timeout | Times out (confirms bug) |
| Small Batch (Fix #1) | 5 | <60s | All complete, <1.5s each |
| Medium Batch (Fix #2) | 20 | <180s | All complete, <1.0s each |
| Large Batch (All Fixes) | 50 | <300s | All complete, <0.8s each, <25 threads |
| API Integration | - | <30s | All endpoints return 200 |

