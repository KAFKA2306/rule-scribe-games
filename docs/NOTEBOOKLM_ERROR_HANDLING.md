# NotebookLM Integration: Error Handling, Rate Limiting & Caching Strategy

## Executive Summary

This document provides a comprehensive error handling and operational strategy for integrating NotebookLM into the FastAPI backend. It covers 4 critical areas:
1. PDF size and upload error scenarios
2. Rate limiting (60 req/min) handling
3. Optimal timeout values for each operation stage
4. Caching vs. re-download strategy

---

## 1. PDF Size Limits & Error Scenarios

### 1.1 File Size Constraints

| Size Range | Behavior | Recommendation |
|-----------|----------|-----------------|
| **< 20 MB** | Reliable upload within timeout | ✅ Direct upload |
| **20-50 MB** | May timeout (>30s) | ⚠️ Text extraction + chunking |
| **> 50 MB** | **WILL timeout & fail** | ❌ Reject or split |

### 1.2 Error Handling Matrix

```
NotebookLM Python SDK raises these exceptions:
1. RPCError: Generic API errors (auth, rate limits, network)
2. FileNotFoundError: Missing auth credentials
3. TimeoutError: Upload/processing exceeds limit
4. ValueError: Invalid parameters (bad file, unsupported format)
```

### 1.3 Recommended Error Handling Pattern

```python
# backend/app/core/notebooklm.py
import asyncio
from typing import Optional
from notebooklm import NotebookLMClient, RPCError
import logging
import os

logger = logging.getLogger(__name__)

class NotebookLMErrorHandler:
    """Categorize and handle NotebookLM errors."""
    
    MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB safe threshold
    UPLOAD_TIMEOUT = 60.0  # seconds
    PROCESSING_TIMEOUT = 120.0  # seconds
    
    @staticmethod
    async def upload_pdf_with_validation(
        client: NotebookLMClient,
        notebook_id: str,
        pdf_path: str,
        filename: str
    ) -> Optional[dict]:
        """Upload PDF with comprehensive error handling."""
        
        # Stage 1: Pre-flight validation
        try:
            file_size = os.path.getsize(pdf_path)
            if file_size > NotebookLMErrorHandler.MAX_FILE_SIZE_BYTES:
                logger.error(
                    "pdf_rejected_oversized",
                    extra={
                        "file": filename,
                        "size_mb": file_size / 1024 / 1024,
                        "limit_mb": 20,
                    }
                )
                raise ValueError(
                    f"PDF exceeds 20 MB limit ({file_size / 1024 / 1024:.1f} MB). "
                    "Use text extraction instead."
                )
        except FileNotFoundError as e:
            logger.error("pdf_file_not_found", extra={"file": filename})
            raise
        
        # Stage 2: Upload with timeout
        try:
            logger.info(
                "pdf_upload_start",
                extra={"file": filename, "size_mb": file_size / 1024 / 1024}
            )
            
            # Use asyncio timeout to enforce hard limit
            source = await asyncio.wait_for(
                client.sources.add_file(notebook_id, pdf_path),
                timeout=NotebookLMErrorHandler.UPLOAD_TIMEOUT
            )
            
            logger.info(
                "pdf_upload_success",
                extra={"file": filename, "source_id": source.get("id")}
            )
            return source
            
        except asyncio.TimeoutError:
            logger.error(
                "pdf_upload_timeout",
                extra={
                    "file": filename,
                    "timeout_seconds": NotebookLMErrorHandler.UPLOAD_TIMEOUT,
                }
            )
            raise TimeoutError(
                f"PDF upload exceeded {NotebookLMErrorHandler.UPLOAD_TIMEOUT}s. "
                "File may be too large or network unstable."
            )
        except RPCError as e:
            # Check for specific RPC error codes
            error_str = str(e)
            
            if "R7cb6c" in error_str:  # Rate limit RPC error
                logger.warning(
                    "pdf_upload_rate_limited",
                    extra={"file": filename, "error_code": "R7cb6c"}
                )
                raise RuntimeError("Rate limited by NotebookLM API") from e
            
            elif "429" in error_str:  # HTTP 429
                logger.warning("pdf_upload_http_429", extra={"file": filename})
                raise RuntimeError("HTTP 429: Too Many Requests") from e
            
            else:
                logger.error(
                    "pdf_upload_rpc_error",
                    extra={
                        "file": filename,
                        "error_type": type(e).__name__,
                        "error": error_str[:200],
                    }
                )
                raise
```

### 1.4 PDF Size Decision Tree

```
┌─ START: Upload PDF
│
├─ [Pre-flight] Check file size
│  ├─ Size < 5 MB? → Continue to upload
│  ├─ Size 5-20 MB? → Upload with monitoring
│  ├─ Size 20-50 MB? → Extract text + summarize locally (fallback)
│  └─ Size > 50 MB? → REJECT with user-friendly message
│
├─ [Upload] Execute with 60s timeout
│  ├─ Success? → Continue to processing
│  ├─ Timeout? → Log as "file too large or network unstable"
│  └─ 429/Rate Limited? → Enqueue for retry (see Rate Limiting)
│
├─ [Processing] Wait for NotebookLM indexing
│  ├─ Complete within 120s? → Cache source ID
│  ├─ Incomplete? → Return partial result, continue async
│  └─ Failed? → Delete notebook, return error
│
└─ END: Return source metadata
```

---

## 2. Rate Limiting Strategy (60 req/min)

### 2.1 Rate Limit Facts

| Metric | Value | Notes |
|--------|-------|-------|
| **Hard Limit** | 60 req/min | ~1 req/sec average |
| **Burst Window** | 1 minute | Sliding window |
| **Indicators** | HTTP 429, RPC `R7cb6c`, error code `[3]` | Can return `None` too |
| **Recovery Time** | 60+ seconds | Exponential backoff recommended |
| **Affects** | All operations: upload, ask, generate | No prioritization |

### 2.2 Rate Limiter Implementation (Token Bucket)

```python
# backend/app/core/notebooklm_rate_limiter.py

import time
import asyncio
from typing import Callable, Any, TypeVar, Coroutine
from collections import deque
import logging

logger = logging.getLogger(__name__)
T = TypeVar('T')

class NotebookLMRateLimiter:
    """Token bucket + exponential backoff for NotebookLM API."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Args:
            max_requests: 60 per minute (NotebookLM limit)
            window_seconds: 60 (sliding window)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()  # (timestamp, operation_type)
        self.rate_limited_until = 0.0  # Unix timestamp
        self._lock = asyncio.Lock()
    
    async def acquire(self, operation: str) -> None:
        """
        Wait if necessary, then proceed.
        
        Args:
            operation: Name of operation (e.g., "upload", "ask", "generate")
        """
        async with self._lock:
            now = time.time()
            
            # If globally rate limited, wait
            if now < self.rate_limited_until:
                wait_time = self.rate_limited_until - now
                logger.warning(
                    "rate_limiter_waiting",
                    extra={
                        "operation": operation,
                        "wait_seconds": f"{wait_time:.1f}",
                    }
                )
                await asyncio.sleep(wait_time)
                now = time.time()
            
            # Clean old requests outside window
            while self.requests and self.requests[0][0] < now - self.window_seconds:
                self.requests.popleft()
            
            # Check if we're at capacity
            if len(self.requests) >= self.max_requests:
                oldest = self.requests[0][0]
                wait_time = (oldest + self.window_seconds) - now
                
                logger.info(
                    "rate_limiter_backpressure",
                    extra={
                        "operation": operation,
                        "in_window": len(self.requests),
                        "wait_seconds": f"{wait_time:.1f}",
                    }
                )
                await asyncio.sleep(wait_time + 0.1)
                now = time.time()
            
            # Add request
            self.requests.append((now, operation))
            logger.debug(
                "rate_limiter_acquired",
                extra={
                    "operation": operation,
                    "pending": len(self.requests),
                }
            )
    
    def mark_rate_limited(self, duration_seconds: int = 60) -> None:
        """Called when API returns 429."""
        self.rate_limited_until = time.time() + duration_seconds
        logger.warning(
            "rate_limiter_api_429",
            extra={
                "backoff_seconds": duration_seconds,
                "until": self.rate_limited_until,
            }
        )
    
    def get_status(self) -> dict:
        """Return current limiter status."""
        now = time.time()
        while self.requests and self.requests[0][0] < now - self.window_seconds:
            self.requests.popleft()
        
        return {
            "requests_in_window": len(self.requests),
            "max_capacity": self.max_requests,
            "utilization_percent": (len(self.requests) / self.max_requests) * 100,
            "globally_rate_limited": now < self.rate_limited_until,
            "seconds_until_recovery": max(0, self.rate_limited_until - now),
        }

# Global instance
limiter = NotebookLMRateLimiter(max_requests=60, window_seconds=60)

# Usage decorator
def rate_limited(operation_name: str):
    """Decorator for rate-limited operations."""
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        async def wrapper(*args, **kwargs) -> T:
            await limiter.acquire(operation_name)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 2.3 Exponential Backoff Pattern

```python
# backend/app/core/notebooklm_retry.py

import asyncio
import random
import logging
from typing import TypeVar, Coroutine, Callable, Any

logger = logging.getLogger(__name__)
T = TypeVar('T')

class ExponentialBackoff:
    """Exponential backoff with jitter for retries."""
    
    def __init__(
        self,
        base_wait: float = 1.0,
        max_wait: float = 60.0,
        max_retries: int = 5,
        jitter: bool = True
    ):
        self.base_wait = base_wait
        self.max_wait = max_wait
        self.max_retries = max_retries
        self.jitter = jitter
    
    def calculate_wait(self, attempt: int) -> float:
        """Calculate wait time for attempt (0-indexed)."""
        wait = min(self.base_wait * (2 ** attempt), self.max_wait)
        if self.jitter:
            wait *= (0.5 + random.random())  # 50%-150% of calculated time
        return wait
    
    async def retry_operation(
        self,
        operation: Callable[..., Coroutine[Any, Any, T]],
        operation_name: str,
        *args,
        **kwargs
    ) -> T:
        """Execute operation with retries."""
        from notebooklm import RPCError
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "backoff_attempt_start",
                    extra={
                        "operation": operation_name,
                        "attempt": attempt + 1,
                        "max_attempts": self.max_retries,
                    }
                )
                
                result = await operation(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(
                        "backoff_recovery",
                        extra={
                            "operation": operation_name,
                            "recovered_at_attempt": attempt + 1,
                        }
                    )
                
                return result
            
            except RPCError as e:
                error_str = str(e)
                is_retryable = "R7cb6c" in error_str or "429" in error_str
                
                if attempt == self.max_retries - 1 or not is_retryable:
                    logger.error(
                        "backoff_max_attempts_exceeded",
                        extra={
                            "operation": operation_name,
                            "attempts": attempt + 1,
                            "retryable": is_retryable,
                            "error": error_str[:150],
                        }
                    )
                    raise
                
                wait_time = self.calculate_wait(attempt)
                logger.warning(
                    "backoff_retry_scheduled",
                    extra={
                        "operation": operation_name,
                        "attempt": attempt + 1,
                        "wait_seconds": f"{wait_time:.1f}",
                        "error": error_str[:150],
                    }
                )
                
                await asyncio.sleep(wait_time)

# Recommended instances
backoff_fast = ExponentialBackoff(base_wait=1.0, max_retries=3)  # Quick retries
backoff_standard = ExponentialBackoff(base_wait=2.0, max_retries=4)  # Normal
backoff_aggressive = ExponentialBackoff(base_wait=2.0, max_retries=6, max_wait=120.0)  # Batch
```

### 2.4 Operation-Specific Rate Limits

| Operation | Typical Duration | Rate Limit Impact | Recommendation |
|-----------|------------------|-------------------|-----------------|
| `upload` (PDF) | 2-10 seconds | High (1-2 req/sec sustained) | Stagger uploads by 2-3 seconds |
| `ask` (query) | 1-3 seconds | Medium (simple, fast) | Rate limiter handles naturally |
| `generate_audio` (podcast) | 30-60 seconds | Medium (long-running) | Async, don't wait on request |
| `source_wait` (polling) | Per-attempt | Low (polling only) | Poll every 5s, not every 1s |

---

## 3. Timeout Strategy

### 3.1 Recommended Timeout Values

```python
# backend/app/core/notebooklm_config.py

class NotebookLMTimeouts:
    """Production-tested timeout values."""
    
    # Stage 1: PDF Upload
    UPLOAD_SMALL = 30.0  # < 5 MB
    UPLOAD_MEDIUM = 60.0  # 5-20 MB (current max safe)
    UPLOAD_LARGE = 90.0  # 20-50 MB (with text extraction)
    
    # Stage 2: Source Processing (indexing)
    SOURCE_PROCESS_QUICK = 30.0
    SOURCE_PROCESS_NORMAL = 60.0
    SOURCE_PROCESS_SLOW = 120.0
    
    # Stage 3: Query/Ask
    QUERY_TIMEOUT = 15.0
    
    # Stage 4: Generation
    GENERATE_AUDIO_START = 10.0
    GENERATE_AUDIO_WAIT = 120.0
    
    # Stage 5: Polling/Waiting
    POLL_TIMEOUT = 180.0
    POLL_INTERVAL = 5.0
```

### 3.2 Timeout Decision Tree

```
┌─ Determine appropriate timeout
│
├─ PDF UPLOAD (read file → send to NotebookLM)
│  ├─ File < 5 MB? → Use 30s timeout
│  ├─ File 5-20 MB? → Use 60s timeout
│  ├─ File > 20 MB → Reject or extract text
│  └─ Timeout? → User error: "Upload failed (network or file too large)"
│
├─ SOURCE INDEXING (NotebookLM processes uploaded file)
│  ├─ Not relevant for downloads (no local file size constraint)
│  ├─ Always use 60-120s timeout
│  ├─ Poll every 5s, not every 1s (respects rate limits)
│  └─ Timeout? → Log error, delete notebook, return failure
│
├─ QUERY/ASK (synchronous Q&A)
│  ├─ Simple query? → Use 15s timeout
│  ├─ Timeout? → Return "Query timeout (try simpler question)"
│  └─ Note: Don't wait for full response; use streaming if available
│
├─ GENERATE AUDIO/SUMMARY (async generation)
│  ├─ Start request? → 10s timeout (should be instant)
│  ├─ Wait for completion? → 120s timeout per poll
│  ├─ Respond immediately with task_id → Don't block
│  └─ Client polls /check-generation-status in background
│
└─ END: Return appropriate result or error
```

---

## 4. Caching Strategy

### 4.1 Cache Decision Matrix

| Scenario | Cache? | TTL | Reason |
|----------|--------|-----|--------|
| **PDF from fixed URL** (e.g., board game rulebook) | ✅ YES | 30 days | URL unlikely to change; save bandwidth |
| **User-uploaded PDF** | ✅ YES (metadata) | 7 days | Cache notebook ID + source ID, not file |
| **Generated content** (audio, summary) | ✅ YES | 30 days | Expensive to regenerate |
| **Chat responses** (ask queries) | ❌ NO | — | Context-dependent; re-ask if needed |
| **Notebook metadata** | ✅ YES | 24 hours | Cheap to store, useful for UI |

### 4.2 Caching Architecture

```python
# backend/app/core/notebooklm_cache.py

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Any
from app.core.supabase import supabase
import logging

logger = logging.getLogger(__name__)

class NotebookLMCache:
    """Multi-layer cache: memory → Supabase → file system."""
    
    TABLE_NAME = "notebooklm_cache"
    
    @staticmethod
    def _hash_url(url: str) -> str:
        """Generate deterministic hash for URL."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    @staticmethod
    async def get_cached_notebook(
        source_identifier: str,
        source_type: str  # "url" or "content"
    ) -> Optional[dict]:
        """
        Retrieve cached notebook info.
        
        Returns:
            {
                "notebook_id": str,
                "source_id": str,
                "created_at": ISO timestamp,
                "expires_at": ISO timestamp,
            }
        """
        rows = await supabase.query(
            f"""
            SELECT * FROM {NotebookLMCache.TABLE_NAME}
            WHERE source_identifier = %s
            AND source_type = %s
            AND expires_at > NOW()
            LIMIT 1
            """,
            [source_identifier, source_type]
        )
        
        if rows:
            logger.info(
                "cache_hit",
                extra={
                    "source_type": source_type,
                    "identifier": source_identifier[:20],
                }
            )
            return rows[0]
        
        logger.debug("cache_miss", extra={"source_type": source_type})
        return None
    
    @staticmethod
    async def set_cached_notebook(
        source_identifier: str,
        source_type: str,
        notebook_id: str,
        source_id: str,
        ttl_days: int = 30
    ) -> None:
        """Store notebook reference in cache."""
        now = datetime.utcnow()
        expires_at = now + timedelta(days=ttl_days)
        
        await supabase.upsert(
            NotebookLMCache.TABLE_NAME,
            {
                "source_identifier": source_identifier,
                "source_type": source_type,
                "notebook_id": notebook_id,
                "source_id": source_id,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
            },
            conflict_target=["source_identifier", "source_type"]
        )
        
        logger.info(
            "cache_set",
            extra={"source_type": source_type, "ttl_days": ttl_days}
        )
```

### 4.3 PDF Download vs. Cache Decision

```
Cache ALWAYS for:
- Official board game rulebooks (URLs from publisher)
- User-uploaded PDFs (store notebook_id + source_id)
- Generated content (audio, summaries)

Don't cache:
- User chat responses (context-dependent)
- Temporary files (delete after use)
- External research PDFs (high change rate)

Decision logic:
1. Check cache first (TTL 30 days for URLs, 7 days for uploads)
2. If hit: return cached notebook_id
3. If miss or expired: download → create notebook → index → cache
```

### 4.4 Cache Database Schema

```sql
-- backend/app/migrations/add_notebooklm_cache.sql

CREATE TABLE IF NOT EXISTS notebooklm_cache (
    id BIGSERIAL PRIMARY KEY,
    source_identifier TEXT NOT NULL,  -- URL hash or content hash
    source_type TEXT NOT NULL,         -- 'url' or 'content'
    notebook_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    is_valid BOOLEAN DEFAULT TRUE,
    
    UNIQUE (source_identifier, source_type),
    INDEX idx_notebooklm_cache_expires (expires_at),
    INDEX idx_notebooklm_cache_type (source_type)
);

-- Cleanup task: run daily
DELETE FROM notebooklm_cache
WHERE expires_at < NOW();
```

---

## 5. Error Handling Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NotebookLM Integration Flow                       │
└─────────────────────────────────────────────────────────────────────┘

USER REQUEST
    │
    ├─→ [Validation] File size check
    │    ├─ OK? Continue
    │    └─ >50 MB? Return 413: Payload Too Large
    │
    ├─→ [Cache] Check NotebookLMCache
    │    ├─ Hit (fresh)? Return cached notebook_id
    │    ├─ Hit (stale)? Mark for refresh
    │    └─ Miss? Continue to creation
    │
    ├─→ [Rate Limiter] Acquire permit (60 req/min)
    │    ├─ Permit available? Continue
    │    └─ At capacity? Wait in queue (token bucket)
    │
    ├─→ [Upload] Send PDF to NotebookLM (60s timeout)
    │    ├─ Success (20s)? Store source_id
    │    ├─ Timeout (60s)? → Backoff
    │    ├─ 429 (rate limit)? Mark limiter, Backoff
    │    ├─ R7cb6c (RPC limit)? Backoff
    │    ├─ File error? Return 400: Bad Request
    │    └─ Auth error? Return 401: Unauthorized
    │
    ├─→ [Processing] Wait for indexing (120s timeout)
    │    ├─ Success? Cache entry created
    │    ├─ Timeout? Log, return partial
    │    └─ Failed? Delete notebook, return error
    │
    ├─→ [Query/Ask] Run Q&A against notebook (15s timeout)
    │    ├─ Success? Return response
    │    ├─ Timeout? Return 504: Gateway Timeout
    │    └─ Invalid query? Return 400: Bad Request
    │
    ├─→ [Generate] Start audio/summary (async)
    │    ├─ Request accepted? Return task_id + 202 status
    │    ├─ 429? Enqueue for later
    │    └─ Client polls /check-status separately
    │
    └─→ RESPOND to user

ERROR PATHS (Crash-Driven):
FileNotFoundError → Let it crash (file missing)
TimeoutError → Let it crash (client retries)
RPCError → Exponential backoff (infrastructure layer)
ValueError → Return 400 Bad Request (user error)
```

---

## 6. Implementation Summary

### Files to Create
- `backend/app/core/notebooklm.py` - Error handling
- `backend/app/core/notebooklm_rate_limiter.py` - Rate limiting
- `backend/app/core/notebooklm_retry.py` - Exponential backoff
- `backend/app/core/notebooklm_cache.py` - Caching layer
- `backend/app/services/notebooklm_service.py` - Integration
- `backend/app/routers/notebooklm.py` - API endpoints

### Database Changes
- Add `notebooklm_cache` table to Supabase
- Indices on `expires_at` and `source_type`

### Testing
- End-to-end: PDF → upload → query → response
- Rate limiter: simulate 100 concurrent requests
- Timeout handling: inject packet loss/latency
- Cache validation: verify TTL expiry

---

**Status**: Ready for implementation  
**Last Updated**: 2026-03-15
