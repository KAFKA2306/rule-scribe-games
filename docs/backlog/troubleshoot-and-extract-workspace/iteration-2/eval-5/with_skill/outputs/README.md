# Database Infrastructure Troubleshooting - Complete Diagnostic & Fix

**Problem:** Batch PDF extraction script processes 50+ games but times out at game 15-20 with "connection pool exceeded" errors.

**Solution:** This package contains complete diagnostic, root cause analysis, and code fixes.

---

## Contents

### 📋 Diagnostics & Analysis
- **`database-infrastructure-diagnostic.md`** (12 KB)
  - Root cause analysis (connection pool exhaustion, sync-to-async mismatch, lack of rate limiting)
  - 4-step diagnostic checklist
  - Environment configuration
  - Monitoring recommendations

### 🔧 Code Fixes (4 implementations)

1. **`supabase_with_semaphore.py`** (Quick fix, 5 minutes)
   - Add asyncio.Semaphore to limit concurrent operations
   - Apply to all Supabase methods
   - Max 5 concurrent operations (configurable)

2. **`supabase_pool.py`** (Optional: Connection pooling wrapper)
   - Reusable client instance
   - Timeout configuration
   - Future-proof design

3. **`batch_processor.py`** (Robust batch processing)
   - Batch processing with rate limiting
   - Retry logic with exponential backoff
   - Error handling modes (raise/skip/log)
   - Works with 50-500 items

4. **`retry.py`** (Resilience utilities)
   - Exponential backoff with jitter
   - Works with async and sync functions
   - Configurable delay and max attempts

### 📝 Implementation Guides

- **`IMPLEMENTATION_STEPS.md`** (Step-by-step, 4 phases)
  - Phase 1: Emergency fix (10 minutes) — Use safe shell script
  - Phase 2: Short-term fix (30 minutes) — Apply semaphore
  - Phase 3: Medium-term fix (2 hours) — Add pooling & monitoring
  - Phase 4: Validation & testing
  - Rollback plan & troubleshooting

### 🚀 Ready-to-Use Scripts

- **`batch_update_safe.sh`** (Bash shell script)
  - Drop-in replacement for hanging scripts
  - Sequential processing with 1-second delays
  - No Python refactoring needed
  - Recommended for immediate use

- **`batch_update_safe_example.py`** (Python example)
  - Shows how to use batch_processor and retry
  - Update 50+ games safely
  - Full error handling and logging

---

## Quick Start

### Immediate Fix (Right Now)

```bash
# Use the safe shell script — no code changes
cd /home/kafka/projects/rule-scribe-games
bash troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/batch_update_safe.sh
```

Expected: All 50 games processed in 50-60 seconds, no timeouts.

### Short-term Fix (This Week)

```bash
# Apply semaphore-based concurrency control
cp troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/supabase_with_semaphore.py app/core/supabase.py

# Copy batch processor utilities
cp troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/batch_processor.py app/services/
cp troubleshoot-and-extract-workspace/iteration-2/eval-5/with_skill/outputs/retry.py app/utils/

# Update your batch scripts to use batch_process()
# See IMPLEMENTATION_STEPS.md for details
```

Then test:
```bash
task dev:backend &
python scripts/your_batch_script.py  # Now uses batch_process
```

---

## Root Causes (Summary)

1. **Connection Pool Exhaustion**: Each async operation spawns a thread. 50 games × 4 ops/game = 200 threads competing for 10-20 connections.

2. **Sync-to-Async Mismatch**: `anyio.to_thread.run_sync()` creates new threads without reuse. Threads accumulate until connection pool is exhausted.

3. **No Rate Limiting**: Batch script loops rapidly without delays, overwhelming the pool.

4. **Silent Exception Handling**: `except Exception: pass` hides the real error (connection timeout), making debugging hard.

---

## Key Recommendations

| Phase | Effort | Impact | Timeline |
|-------|--------|--------|----------|
| Phase 1: Shell script | 1 min | Immediate relief | Now |
| Phase 2: Semaphore | 5 min | Prevents pool exhaustion | Today |
| Phase 3: Monitoring | 2 hours | Production-grade visibility | Week 1 |

---

## Files You Need to Modify

### Minimum Changes (Phase 2)

1. Replace `app/core/supabase.py` with `supabase_with_semaphore.py`
2. Add `batch_processor.py` to `app/services/`
3. Add `retry.py` to `app/utils/`
4. Update batch scripts to use `batch_process()`

### Recommended Changes (Phase 3)

5. Add `.env` pool configuration
6. Add health check endpoint
7. Add metrics logging

---

## Validation Checklist

After implementation, verify:

- [ ] No "connection pool exceeded" errors in logs
- [ ] Script processes 50 games without timeout
- [ ] All games updated (100% success rate)
- [ ] Execution time < 5 minutes for 50 games
- [ ] Database responsive during batch processing
- [ ] Health check endpoint returns `{status: "healthy"}`

---

## Troubleshooting

### Script still hangs after Phase 2?

Check that you're using the new `supabase.py` with semaphore:
```bash
grep "asyncio.Semaphore" app/core/supabase.py
# Should see: _semaphore = asyncio.Semaphore(5)
```

If missing, the old code is still running.

### "batch_process not found" error?

Check batch_processor.py was copied:
```bash
python -c "from app.services.batch_processor import batch_process; print('OK')"
```

### Still too slow?

Increase concurrency:
```bash
# In app/core/supabase.py:
_semaphore = asyncio.Semaphore(10)  # Increase from 5

# In batch_process calls:
batch_size=10,  # Increase from 5
delay_between_batches=0.2,  # Decrease from 0.5
```

Monitor with `/health/db` endpoint to find the right balance.

---

## File Organization

```
outputs/
├── README.md                              (This file)
├── database-infrastructure-diagnostic.md  (Root cause, monitoring)
├── IMPLEMENTATION_STEPS.md                (4-phase guide with checklists)
├── supabase_with_semaphore.py            (Phase 2: semaphore fix)
├── supabase_pool.py                      (Phase 3: pooling)
├── batch_processor.py                    (Batch processing utilities)
├── retry.py                              (Retry utilities)
├── batch_update_safe.sh                  (Phase 1: emergency fix)
└── batch_update_safe_example.py          (Example using new patterns)
```

---

## Next Steps

1. **Read** `database-infrastructure-diagnostic.md` to understand the root cause
2. **Choose a phase:**
   - Emergency? → Run `batch_update_safe.sh` (Phase 1)
   - Have 30 minutes? → Apply semaphore (Phase 2)
   - Production-ready? → Full implementation (Phases 2-3)
3. **Follow** `IMPLEMENTATION_STEPS.md` for exact commands
4. **Validate** with the checklist
5. **Reference** code comments in fixed files for explanations

---

## Questions Answered by This Package

**Q: Why does it fail at game 15-20?**
A: Thread pool (8 workers) × 4 ops/game = 32 threads by game 8. Supabase pool (10-20 connections) exhausted. See diagnostic.

**Q: What's the fastest fix?**
A: `bash batch_update_safe.sh` — sequential processing, no code changes, 50-60 seconds.

**Q: What's the production-grade fix?**
A: Phase 2 + Phase 3 — semaphore + batch processor + monitoring = scalable to 500+ items.

**Q: Why not use an ORM?**
A: Supabase SDK doesn't support connection pooling. Direct client is necessary; we compensate with semaphores.

**Q: Should I add retry logic?**
A: Yes, see `retry.py` and `batch_processor.py` — handles transient failures gracefully.

---

## Support

- **Diagnostic logs**: Check `batch.log` from script output
- **Health check**: `curl http://localhost:8000/health/db`
- **Full trace**: Run with `PYTHONUNBUFFERED=1` to see output in real-time
- **Still stuck?** Read the "Gotchas" section in `database-infrastructure-diagnostic.md`

---

Generated: March 15, 2026
For: rule-scribe-games batch PDF extraction pipeline
