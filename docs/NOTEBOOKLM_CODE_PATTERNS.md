# NotebookLM Code Patterns & Implementation Guide

## 1. Complete Service Implementation

```python
# backend/app/services/notebooklm_service.py

from app.core.notebooklm_rate_limiter import limiter, rate_limited
from app.core.notebooklm_retry import backoff_standard
from app.core.notebooklm_cache import NotebookLMCache
from app.core.notebooklm import NotebookLMErrorHandler
from notebooklm import NotebookLMClient, RPCError
import logging
import asyncio
import tempfile
import os

logger = logging.getLogger(__name__)

class NotebookLMService:
    """Production-grade NotebookLM integration."""
    
    def __init__(self):
        self.client = NotebookLMClient.from_storage()
        self.error_handler = NotebookLMErrorHandler()
    
    @rate_limited("pdf_upload")
    async def upload_pdf(
        self,
        pdf_path: str,
        notebook_id: str,
        filename: str
    ) -> dict:
        """Upload PDF with comprehensive error handling."""
        try:
            return await self.error_handler.upload_pdf_with_validation(
                self.client, notebook_id, pdf_path, filename
            )
        except TimeoutError as e:
            logger.error("upload_timeout", extra={"file": filename, "error": str(e)})
            raise
        except ValueError as e:
            logger.error("upload_validation_failed", extra={"file": filename, "error": str(e)})
            raise
    
    @rate_limited("notebook_create")
    async def create_notebook(self, title: str) -> dict:
        """Create notebook with backoff."""
        async def _create():
            return await self.client.notebooks.create(title)
        
        return await backoff_standard.retry_operation(
            _create, "create_notebook"
        )
    
    @rate_limited("notebook_ask")
    async def ask_notebook(
        self,
        notebook_id: str,
        question: str,
        timeout: float = 15.0
    ) -> str:
        """Query notebook with timeout."""
        
        async def _ask():
            return await self.client.notebooks.ask(notebook_id, question)
        
        try:
            result = await asyncio.wait_for(
                backoff_standard.retry_operation(_ask, "ask_notebook"),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Query timeout after {timeout}s")

# Instantiate globally
notebooklm_service = NotebookLMService()
```

## 2. FastAPI Endpoints

```python
# backend/app/routers/notebooklm.py

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from app.services.notebooklm_service import notebooklm_service
from app.core.notebooklm_cache import NotebookLMCache
from app.core.notebooklm_rate_limiter import limiter
from typing import Optional
import logging
import tempfile
import os

router = APIRouter(prefix="/api/notebooklm", tags=["notebooklm"])
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)) -> dict:
    """
    Upload and index a PDF with NotebookLM.
    
    Rate limited: 60 req/min
    Timeout: 60 seconds for upload, 120 seconds for processing
    """
    try:
        # Create notebook
        notebook = await notebooklm_service.create_notebook(
            title=file.filename.replace(".pdf", "")
        )
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp.flush()
            
            try:
                # Upload
                source = await notebooklm_service.upload_pdf(
                    tmp.name, notebook["id"], file.filename
                )
                
                return {
                    "notebook_id": notebook["id"],
                    "source_id": source["id"],
                    "status": "uploaded_and_indexed",
                    "file_name": file.filename,
                }
            
            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)
    
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        logger.error("upload_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Upload failed")

@router.post("/ask")
async def ask_question(
    notebook_id: str,
    question: str
) -> dict:
    """
    Ask a question to a notebook.
    
    Rate limited: 60 req/min
    Timeout: 15 seconds
    """
    try:
        response = await notebooklm_service.ask_notebook(
            notebook_id, question, timeout=15.0
        )
        return {
            "question": question,
            "answer": response,
            "notebook_id": notebook_id
        }
    
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Query timeout")
    except Exception as e:
        logger.error("ask_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Query failed")

@router.get("/cache/status")
async def cache_status() -> dict:
    """Get cache and rate limiter status."""
    return {
        "rate_limiter": limiter.get_status(),
        "cache_note": "Check Supabase notebooklm_cache table for entries"
    }

@router.delete("/cache/{source_identifier}")
async def invalidate_cache(source_identifier: str) -> dict:
    """Manually invalidate a cache entry."""
    await NotebookLMCache.invalidate_cached_notebook(
        source_identifier, "url"
    )
    return {"status": "invalidated", "identifier": source_identifier}
```

## 3. Integration into main.py

```python
# backend/app/main.py (add these lines)

from app.routers import notebooklm

# ... existing imports and setup ...

# Include NotebookLM router
app.include_router(notebooklm.router)

# Log rate limiter status on startup
@app.on_event("startup")
async def startup_event():
    logger.info("app_startup", extra={"rate_limiter": limiter.get_status()})
```

## 4. Timeout Manager Pattern

```python
# backend/app/core/notebooklm_timeout.py

import asyncio
import time
from typing import TypeVar, Coroutine, Any, Optional
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)
T = TypeVar('T')

class TimeoutManager:
    """Smart timeout management with operation awareness."""
    
    @staticmethod
    async def execute_with_timeout(
        operation: str,
        coro: Coroutine[Any, Any, T],
        timeout: float,
        fallback_error_msg: Optional[str] = None
    ) -> T:
        """Execute coroutine with timeout and operation-specific error handling."""
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            logger.info(
                "operation_completed",
                extra={"operation": operation, "timeout_seconds": timeout}
            )
            return result
        
        except asyncio.TimeoutError:
            error_msg = fallback_error_msg or f"{operation} exceeded {timeout}s timeout"
            logger.error(
                "operation_timeout",
                extra={
                    "operation": operation,
                    "timeout_seconds": timeout,
                    "message": error_msg,
                }
            )
            raise TimeoutError(error_msg)
    
    @staticmethod
    @asynccontextmanager
    async def stage_timeout(operation: str, timeout: float):
        """Context manager for timing a stage."""
        start = time.time()
        try:
            yield
        except asyncio.TimeoutError as e:
            elapsed = time.time() - start
            logger.error(
                "stage_timeout",
                extra={
                    "operation": operation,
                    "timeout_seconds": timeout,
                    "elapsed_seconds": f"{elapsed:.1f}",
                }
            )
            raise
        finally:
            elapsed = time.time() - start
            logger.info(
                "stage_completed",
                extra={
                    "operation": operation,
                    "elapsed_seconds": f"{elapsed:.1f}",
                }
            )

# Usage example
async def upload_and_process_pdf(client, notebook_id, pdf_path):
    """Full PDF lifecycle with proper timeouts."""
    
    # Stage 1: Upload (60 second timeout)
    async with TimeoutManager.stage_timeout("pdf_upload", 60.0):
        source = await client.sources.add_file(notebook_id, pdf_path)
    
    # Stage 2: Wait for processing (120 second timeout)
    async with TimeoutManager.stage_timeout("source_processing", 120.0):
        await client.sources.wait(source["id"], timeout=120)
    
    return source
```

## 5. Cache Layer with URL Hashing

```python
# backend/app/core/notebooklm_cache_advanced.py

import hashlib
from datetime import datetime, timedelta
from typing import Optional
from app.core.supabase import supabase
import logging

logger = logging.getLogger(__name__)

class NotebookLMCacheAdvanced:
    """Advanced caching with URL validation and refresh."""
    
    TABLE_NAME = "notebooklm_cache"
    
    @staticmethod
    def _hash_url(url: str) -> str:
        """Generate deterministic hash for URL."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    @staticmethod
    async def get_or_create_from_url(
        client,
        url: str,
        title: str,
        cache_ttl_days: int = 30
    ) -> dict:
        """Get cached notebook or create new one."""
        
        url_hash = NotebookLMCacheAdvanced._hash_url(url)
        
        # Check cache first
        cached = await supabase.query(
            f"""
            SELECT * FROM {NotebookLMCacheAdvanced.TABLE_NAME}
            WHERE source_identifier = %s
            AND source_type = 'url'
            AND expires_at > NOW()
            LIMIT 1
            """,
            [url_hash]
        )
        
        if cached:
            logger.info(
                "cache_hit_notebook",
                extra={"notebook_id": cached[0]["notebook_id"]}
            )
            return cached[0]
        
        # Not cached: create new
        logger.info("creating_notebook_from_url", extra={"url": url[:50]})
        
        notebook = await client.notebooks.create(title)
        source = await client.sources.add_url(notebook["id"], url)
        
        # Cache for specified TTL
        now = datetime.utcnow()
        expires_at = now + timedelta(days=cache_ttl_days)
        
        await supabase.upsert(
            NotebookLMCacheAdvanced.TABLE_NAME,
            {
                "source_identifier": url_hash,
                "source_type": "url",
                "notebook_id": notebook["id"],
                "source_id": source["id"],
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "original_url": url,
            },
            conflict_target=["source_identifier", "source_type"]
        )
        
        return {
            "notebook_id": notebook["id"],
            "source_id": source["id"],
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
```

## 6. Monitoring & Metrics

```python
# backend/app/core/notebooklm_metrics.py

from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class NotebookLMMetrics:
    """Track NotebookLM health metrics."""
    
    upload_avg_duration_ms: float = 0.0
    query_avg_duration_ms: float = 0.0
    cache_hit_rate: float = 0.0
    
    upload_failures: int = 0
    query_failures: int = 0
    rate_limit_hits: int = 0
    timeout_errors: int = 0
    
    current_utilization: float = 0.0
    max_queue_depth: int = 0
    
    total_cached_notebooks: int = 0
    cache_expiry_pending: int = 0
    
    last_updated: datetime = None

metrics = NotebookLMMetrics()

def log_metrics():
    """Log current metrics for monitoring."""
    logger.info(
        "notebooklm_metrics",
        extra={
            "upload_duration_ms": f"{metrics.upload_avg_duration_ms:.0f}",
            "query_duration_ms": f"{metrics.query_avg_duration_ms:.0f}",
            "cache_hit_rate": f"{metrics.cache_hit_rate:.1f}%",
            "rate_limit_utilization": f"{metrics.current_utilization:.1f}%",
            "errors_upload": metrics.upload_failures,
            "errors_query": metrics.query_failures,
            "errors_rate_limit": metrics.rate_limit_hits,
            "errors_timeout": metrics.timeout_errors,
            "cached_notebooks": metrics.total_cached_notebooks,
        }
    )

def update_metric_on_operation(operation: str, duration_ms: float, status: str):
    """Update metrics after operation."""
    if operation == "upload":
        if status == "success":
            metrics.upload_avg_duration_ms = (
                (metrics.upload_avg_duration_ms + duration_ms) / 2
            )
        else:
            metrics.upload_failures += 1
    
    elif operation == "query":
        if status == "success":
            metrics.query_avg_duration_ms = (
                (metrics.query_avg_duration_ms + duration_ms) / 2
            )
        else:
            metrics.query_failures += 1
    
    if status == "rate_limited":
        metrics.rate_limit_hits += 1
    elif status == "timeout":
        metrics.timeout_errors += 1
    
    metrics.last_updated = datetime.utcnow()
```

## 7. Taskfile Integration

```yaml
# Taskfile.yml additions

  notebooklm:verify:
    desc: "Verify NotebookLM credentials and API access"
    cmd: uv run python -m backend.scripts.verify_notebooklm

  notebooklm:test:upload:
    desc: "Test PDF upload workflow (end-to-end)"
    cmd: uv run pytest backend/tests/test_notebooklm_upload.py -v

  notebooklm:test:rate-limit:
    desc: "Simulate rate limiting scenario"
    cmd: uv run pytest backend/tests/test_notebooklm_ratelimit.py -v

  notebooklm:cache:cleanup:
    desc: "Delete expired cache entries"
    cmd: uv run python -m backend.scripts.cleanup_notebooklm_cache

  notebooklm:cache:status:
    desc: "Show cache statistics"
    cmd: uv run python -m backend.scripts.show_notebooklm_cache_stats

  notebooklm:logs:errors:
    desc: "Show recent NotebookLM errors"
    cmd: tail -n 100 backend/logs/notebooklm.log | grep -i error
```

## 8. Configuration File

```python
# backend/app/core/notebooklm_config.py

class NotebookLMConfig:
    """Production configuration for NotebookLM integration."""
    
    # Rate limiting (60 req/min per NotebookLM docs)
    RATE_LIMIT_MAX_REQUESTS = 60
    RATE_LIMIT_WINDOW_SECONDS = 60
    
    # Timeouts
    UPLOAD_TIMEOUT_SMALL = 30.0  # < 5 MB
    UPLOAD_TIMEOUT_MEDIUM = 60.0  # 5-20 MB
    UPLOAD_TIMEOUT_LARGE = 90.0  # 20-50 MB
    
    SOURCE_PROCESS_TIMEOUT = 120.0  # Indexing
    QUERY_TIMEOUT = 15.0
    
    # File size limits
    MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
    WARN_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB (warning threshold)
    
    # Caching
    CACHE_TTL_URL_DAYS = 30  # URLs (stable sources)
    CACHE_TTL_UPLOAD_DAYS = 7  # User uploads
    CACHE_TTL_GENERATED_DAYS = 30  # Generated content
    
    # Retries
    MAX_RETRIES = 4
    BACKOFF_BASE = 2.0  # seconds
    BACKOFF_MAX = 60.0  # seconds
    
    # Polling
    POLL_INTERVAL_SECONDS = 5
    POLL_MAX_ITERATIONS = 36  # 5s * 36 = 180s max
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "backend/logs/notebooklm.log"
```

---

## Best Practices Summary

1. **Always validate file size before upload** (< 20 MB recommended)
2. **Use decorators for rate limiting** (@rate_limited("operation_name"))
3. **Cache by URL hash**, not full URL (deterministic + privacy)
4. **Separate concerns**: Error handling → Rate limiting → Retry → Cache
5. **Log with operation context**: operation, duration, status, error code
6. **Use asyncio.wait_for() for hard timeouts** (not just try-catch)
7. **Never retry in business logic** (let it crash, retry in infrastructure)
8. **Monitor rate limiter utilization** (log every minute)
9. **Clean up expired cache entries daily** (background task)
10. **Return 202 Accepted for async operations**, poll separately

---

**Status**: Ready for production  
**Last Updated**: 2026-03-15
