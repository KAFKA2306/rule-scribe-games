# Supabase Connection Pool Monitoring Setup

## Real-Time Monitoring During Batch Processing

### Monitor #1: Active Task Counter

**Purpose**: Verify concurrency limit is working (should never exceed ~5-7).

**Implementation**: Add to batch script
```python
import asyncio
import threading
from datetime import datetime

async def log_metrics(interval_sec: float = 2.0):
    """Log active tasks and threads every N seconds."""
    while True:
        tasks = [t for t in asyncio.all_tasks() if not t.done()]
        threads = threading.enumerate()
        print(f"[{datetime.now().isoformat()}] Tasks: {len(tasks)}, Threads: {len(threads)}, Memory: {get_memory_usage()}MB")
        await asyncio.sleep(interval_sec)

def get_memory_usage():
    import psutil
    process = psutil.Process()
    return process.memory_info().rss // 1024 // 1024
```

**Usage**: Run metrics in background task
```python
async def process_games_with_monitoring(games):
    # Start metrics logging in background
    metrics_task = asyncio.create_task(log_metrics())

    try:
        results = await batch_process(games, process_game_fn)
        return results
    finally:
        metrics_task.cancel()
```

**Expected Output**:
```
[2026-03-15T10:30:15.123456] Tasks: 3, Threads: 12, Memory: 145MB
[2026-03-15T10:30:17.234567] Tasks: 2, Threads: 11, Memory: 146MB
[2026-03-15T10:30:19.345678] Tasks: 5, Threads: 15, Memory: 148MB
```

**Alert Threshold**: Tasks > 10 or Threads > 25 → connection pool likely starved.

---

### Monitor #2: Query Latency Histogram

**Purpose**: Detect slow database queries that consume connections longer.

**Implementation**: Create `app/core/latency.py`
```python
from datetime import datetime
from typing import Dict, List
import statistics

class LatencyTracker:
    def __init__(self):
        self.queries: List[Dict[str, float]] = []

    def record(self, operation: str, latency_sec: float):
        self.queries.append({
            "op": operation,
            "latency": latency_sec,
            "timestamp": datetime.now().isoformat(),
        })

    def stats(self) -> Dict:
        latencies = [q["latency"] for q in self.queries]
        return {
            "count": len(latencies),
            "mean": statistics.mean(latencies) if latencies else 0,
            "median": statistics.median(latencies) if latencies else 0,
            "max": max(latencies) if latencies else 0,
            "p95": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 20 else max(latencies),
        }

    def log_summary(self):
        stats = self.stats()
        print(f"Query stats: mean={stats['mean']:.2f}s, p95={stats['p95']:.2f}s, max={stats['max']:.2f}s")

_tracker = LatencyTracker()

async def track_latency(operation: str, coro):
    import time
    start = time.time()
    try:
        return await coro
    finally:
        latency = time.time() - start
        _tracker.record(operation, latency)
```

**Usage in supabase.py**:
```python
from app.core.latency import track_latency

async def search(query: str) -> list[dict[str, object]]:
    async with _db_semaphore:
        async def _search():
            def _q():
                safe_query = query.replace('"', '\\"')
                term = f"*{safe_query}*"
                return _client.table(_TABLE).select("*").or_(f'title.ilike."{term}",description.ilike."{term}"').execute().data
            return await anyio.to_thread.run_sync(_q)

        return await track_latency("search", _search())
```

**Expected Output** (after 50 games):
```
Query stats: mean=0.45s, p95=1.20s, max=2.80s
```

**Alert Threshold**: p95 > 2.0s → Supabase or network degraded.

---

### Monitor #3: Connection Pool Utilization

**Purpose**: Detect when pool is near capacity.

**Implementation**: Supabase PostgreSQL query
```sql
-- Run in Supabase SQL Editor to check active connections
SELECT
    datname AS database,
    count(*) AS total_connections,
    count(*) FILTER (WHERE state = 'active') AS active,
    count(*) FILTER (WHERE state = 'idle') AS idle,
    count(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_transaction
FROM pg_stat_activity
GROUP BY datname;
```

**Expected Output** (healthy):
```
| database  | total | active | idle | idle_in_xact |
|-----------|-------|--------|------|--------------|
| postgres  | 8     | 2      | 6    | 0            |
| games_db  | 12    | 3      | 9    | 0            |
```

**Alert Thresholds**:
- `total_connections >= 18` (for free tier, 20 max): Pool near capacity
- `idle_in_transaction > 0`: Possible deadlock or very slow query

**Automated Check** (add to batch script):
```python
import asyncio
from app.core import supabase

async def check_pg_pool():
    """Check PostgreSQL pool status."""
    query = """
    SELECT count(*) as total FROM pg_stat_activity
    WHERE datname = 'postgres'
    """
    # Requires direct SQL access; show warning if unavailable
    logger.info("⚠️  Run this in Supabase SQL Editor to check pool status (cannot query from app)")
```

---

### Monitor #4: Error Rate & Type Distribution

**Purpose**: Categorize failures (timeout vs connection vs other).

**Implementation**: Enhanced error logging
```python
from enum import Enum
from collections import Counter
import logging

class ErrorCategory(Enum):
    TIMEOUT = "timeout"
    CONNECTION_POOL = "connection_pool"
    NETWORK = "network"
    VALIDATION = "validation"
    OTHER = "other"

class ErrorTracker:
    def __init__(self):
        self.errors: Counter = Counter()
        self.logger = logging.getLogger("error_tracker")

    def categorize(self, error: Exception) -> ErrorCategory:
        msg = str(error).lower()
        if "timeout" in msg or "timed out" in msg:
            return ErrorCategory.TIMEOUT
        elif "connection" in msg or "pool" in msg or "too many connections" in msg:
            return ErrorCategory.CONNECTION_POOL
        elif "network" in msg or "connection refused" in msg:
            return ErrorCategory.NETWORK
        elif "validation" in msg or "not found" in msg:
            return ErrorCategory.VALIDATION
        else:
            return ErrorCategory.OTHER

    def record(self, error: Exception):
        cat = self.categorize(error)
        self.errors[cat.value] += 1
        self.logger.error(f"[{cat.value}] {error}")

    def summary(self):
        total = sum(self.errors.values())
        pct = {k: (v/total*100) if total > 0 else 0 for k, v in self.errors.items()}
        return {
            "total_errors": total,
            "by_category": dict(self.errors),
            "by_percentage": pct,
        }

_error_tracker = ErrorTracker()

async def process_with_error_tracking(game):
    try:
        return await process_game(game)
    except Exception as e:
        _error_tracker.record(e)
        raise
```

**Expected Output** (after 50-game batch):
```python
summary = _error_tracker.summary()
# {
#     "total_errors": 3,
#     "by_category": {"timeout": 2, "connection_pool": 1},
#     "by_percentage": {"timeout": 66.7, "connection_pool": 33.3}
# }
```

**Interpretation**:
- Mostly `timeout` → Supabase or network slow (increase timeouts or reduce batch size)
- Mostly `connection_pool` → Fix #1 (semaphore) not working; check limit is 3
- Mostly `validation` → Bad data; inspect game records

---

### Monitor #5: Batch Progress Dashboard

**Purpose**: Visual feedback during long 50+ game runs.

**Implementation**: Rich progress bar
```python
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn
from rich.live import Live
from rich.table import Table

async def batch_process_with_progress(games):
    with Progress(
        BarColumn(bar_width=40),
        DownloadColumn(),
        TransferSpeedColumn(),
        refresh_per_second=2,
    ) as progress:
        task = progress.add_task("[cyan]Processing games...", total=len(games))

        results = []
        for game in games:
            try:
                result = await process_game(game)
                results.append(result)
                progress.update(task, advance=1)
            except Exception as e:
                progress.print(f"❌ {game['title']}: {e}")
                progress.update(task, advance=1)

        return results
```

**Terminal Output**:
```
Processing games... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  42/50 │ 1.2 MB/s
```

---

### Monitor #6: Connection Pool Metrics via Supabase Dashboard

**Manual Check** (every 10 games during batch):

1. **Navigate**: Project Dashboard → Database → Logs → Connections
2. **Filter**: Last 5 minutes
3. **Check**: Connection count trend (should stay flat)

**What to look for**:
- **Good**: Steady 8-10 connections, mostly idle
- **Bad**: Climbing from 8 → 15 → 20 (pool exhaustion in progress)
- **Ugly**: Flat-lined at 20+ (pool maxed out, new queries queued)

---

## Monitoring Checklist During Batch Run

```bash
# Terminal 1: Run batch script with debug logging
export LOG_LEVEL=DEBUG
python scripts/batch_pdf_extract.py 2>&1 | tee batch_$(date +%s).log

# Terminal 2: Monitor active processes (every 5s)
watch -n5 "echo '=== THREADS ===' && ps aux | grep python | wc -l && echo '=== MEMORY ===' && ps aux | grep batch_pdf | grep -v grep | awk '{sum += \$6} END {print sum / 1024 \" MB\"}'"

# Terminal 3: Tail error logs
tail -f batch_*.log | grep -E "(ERROR|❌|timeout|connection)"

# Terminal 4: Check Supabase dashboard
# Manually refresh every 30 seconds:
# Dashboard → Database → Logs → Connections (watch count)
```

---

## Post-Batch Analysis

After batch completes or fails:

```bash
# 1. Extract error summary
grep -E "(ERROR|❌)" batch_*.log | tail -20

# 2. Calculate success rate
TOTAL=$(grep -c "Starting" batch_*.log)
SUCCESS=$(grep -c "✅" batch_*.log)
echo "Success rate: $SUCCESS/$TOTAL"

# 3. Find slowest game
grep "Completed in" batch_*.log | sort -t' ' -k4 -rn | head -5

# 4. Check final latency stats
grep "Query stats:" batch_*.log | tail -1

# 5. Generate report
cat > batch_report_$(date +%s).txt << EOF
Batch Processing Report
=======================
Start time: $(head -1 batch_*.log)
End time: $(tail -1 batch_*.log)
Total games: $TOTAL
Successful: $SUCCESS
Failed: $((TOTAL - SUCCESS))
Success rate: $((SUCCESS * 100 / TOTAL))%
Peak threads: $(grep "Threads:" batch_*.log | sed 's/.*Threads: //' | sort -n | tail -1)
Max latency: $(grep "Completed in" batch_*.log | sed 's/.*in //' | sed 's/s.*//' | sort -n | tail -1)s
EOF
cat batch_report_*.txt
```

---

## Alert Configuration (Optional: Add to config.yaml)

```yaml
monitoring:
  batch:
    max_tasks_concurrent: 7
    max_threads_total: 25
    max_query_latency_sec: 3.0
    max_error_rate_pct: 10
    alert_webhook: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    check_interval_sec: 10

  alerts:
    - condition: "tasks > max_tasks_concurrent"
      action: "log_warning"
      message: "Concurrency limit approaching"

    - condition: "error_rate > max_error_rate_pct"
      action: "pause_batch"
      message: "Error rate exceeded, pausing for 30s"

    - condition: "query_latency_p95 > max_query_latency_sec"
      action: "log_warning"
      message: "Slow database detected, consider reducing batch_size"
```

---

## Summary: Monitoring Priorities

| Monitor | Effort | Priority | Alert Threshold |
|---------|--------|----------|-----------------|
| Active task counter | Low | CRITICAL | Tasks > 10 |
| Query latency histogram | Medium | HIGH | p95 > 2.0s |
| PG pool status (SQL) | Low | HIGH | Connections > 18 |
| Error rate by category | Medium | MEDIUM | Timeout rate > 20% |
| Progress dashboard | Low | MEDIUM | - (visual only) |
| Supabase dashboard | Low | MEDIUM | Connections climbing |

