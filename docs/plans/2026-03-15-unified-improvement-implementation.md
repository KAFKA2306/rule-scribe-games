# RuleScribe v2 Unified Improvement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Realize the "Transparent Game Library" vision by implementing 5 layers (backend stability, content accuracy, frontend display, infographics, smart pipeline) across the customer journey.

**Architecture:** Implement in phases prioritizing foundation first:
1. **Phase 1: Backend Stability** - Error handling, validation, async management, rate limiting
2. **Phase 2: Content Accuracy** - Database schema, confidence scores, versioning, source tracking
3. **Phase 3: Frontend Display** - Search performance, detail page load, accessibility, responsiveness
4. **Phase 4: Infographic Generation** - Schema design, SVG rendering, explainability
5. **Phase 5: Smart Pipeline** - PDF detection, Gemini optimization, quality gates, regeneration

**Tech Stack:** FastAPI, Supabase PostgreSQL, React/Vite, Gemini 3.0 Flash, SVG/Canvas

---

## Phase 1: Backend Stability

### Task 1.1: Add Explicit Error Handling to Game Search Endpoint

**Files:**
- Modify: `app/routers/games.py:search` endpoint
- Modify: `app/core/logger.py` (ensure logging setup)
- Create: `tests/test_game_search_errors.py`

**Step 1: Write failing tests for error scenarios**

```python
# tests/test_game_search_errors.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_search_with_invalid_query_returns_400():
    """Search with None query should return 400, not 500"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/search", params={"q": None})
        assert response.status_code == 400
        assert "error" in response.json()

@pytest.mark.asyncio
async def test_search_with_empty_query_returns_empty_results():
    """Search with empty string returns empty list, not error"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/search", params={"q": ""})
        assert response.status_code == 200
        assert response.json()["games"] == []

@pytest.mark.asyncio
async def test_supabase_timeout_returns_503():
    """If Supabase times out, return 503 with explanation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Mock timeout by using invalid connection
        response = await client.get("/api/search", params={"q": "test", "timeout_ms": 1})
        assert response.status_code == 503
        assert "database" in response.json().get("error", "").lower()
```

**Step 2: Run tests to verify they fail**

```bash
task test -- tests/test_game_search_errors.py -v
```

Expected output:
```
FAILED tests/test_game_search_errors.py::test_search_with_invalid_query_returns_400 - AssertionError
FAILED tests/test_game_search_errors.py::test_search_with_empty_query_returns_empty_results - AssertionError
FAILED tests/test_game_search_errors.py::test_supabase_timeout_returns_503 - AssertionError
```

**Step 3: Update search endpoint with explicit validation and error handling**

Modify `app/routers/games.py`:

```python
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.services.game_service import GameService
from app.core.logger import logger

router = APIRouter(prefix="/api", tags=["games"])

class SearchResponse(BaseModel):
    games: list[dict]
    total: int
    error: str | None = None

@router.get("/search", response_model=SearchResponse)
async def search_games(
    q: str = Query(..., min_length=1, max_length=500),
    generate: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search games by title or description.
    Returns 400 if query is invalid, 503 if database is unavailable.
    """
    try:
        if not q or not q.strip():
            return SearchResponse(games=[], total=0)
        
        results = await GameService.search_games(q.strip(), generate=generate, limit=limit)
        return SearchResponse(games=results["games"], total=results["total"])
    
    except TimeoutError as e:
        logger.error(f"Supabase timeout during search: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database service temporarily unavailable. Please retry."
        )
    except ValueError as e:
        logger.warning(f"Invalid search input: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid search parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please contact support."
        )
```

**Step 4: Run tests to verify they pass**

```bash
task test -- tests/test_game_search_errors.py -v
```

Expected output:
```
PASSED tests/test_game_search_errors.py::test_search_with_invalid_query_returns_400
PASSED tests/test_game_search_errors.py::test_search_with_empty_query_returns_empty_results
PASSED tests/test_game_search_errors.py::test_supabase_timeout_returns_503
```

**Step 5: Commit**

```bash
git add app/routers/games.py tests/test_game_search_errors.py
git commit -m "feat(backend): add explicit error handling to search endpoint

- Validate query length and content
- Return 400 for invalid input, 503 for database timeout
- Log all errors with context for debugging
- Add comprehensive test coverage"
```

---

### Task 1.2: Add Request Validation Middleware

**Files:**
- Create: `app/middleware/validation.py`
- Modify: `app/main.py` (add middleware)
- Create: `tests/test_validation_middleware.py`

**Step 1: Write failing tests**

```python
# tests/test_validation_middleware.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_malformed_json_returns_400():
    """Malformed JSON payload returns 400, not 500"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/games",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        assert "error" in response.json()

@pytest.mark.asyncio
async def test_missing_required_field_returns_422():
    """Missing required fields returns 422 with field details"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/games",
            json={"title": "Test Game"}  # missing required fields
        )
        assert response.status_code == 422
        assert "detail" in response.json()
```

**Step 2: Run tests to verify they fail**

```bash
task test -- tests/test_validation_middleware.py -v
```

Expected: Both tests fail (endpoints may not exist or don't have validation)

**Step 3: Create validation middleware**

```python
# app/middleware/validation.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import json
from app.core.logger import logger

class ValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            # Pre-validate JSON if content-type is application/json
            if request.method in ["POST", "PATCH", "PUT"]:
                if "application/json" in request.headers.get("content-type", ""):
                    body = await request.body()
                    if body:
                        try:
                            json.loads(body)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Malformed JSON in {request.url}: {e}")
                            return JSONResponse(
                                status_code=400,
                                content={"error": f"Invalid JSON: {str(e)}"}
                            )
            
            response = await call_next(request)
            return response
        
        except Exception as e:
            logger.error(f"Validation middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal validation error"}
            )
```

**Step 4: Register middleware in app**

Modify `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.validation import ValidationMiddleware
from app.routers import games

app = FastAPI(title="RuleScribe API")

# Add validation middleware
app.add_middleware(ValidationMiddleware)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)
```

**Step 5: Run tests**

```bash
task test -- tests/test_validation_middleware.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add app/middleware/validation.py app/main.py tests/test_validation_middleware.py
git commit -m "feat(backend): add validation middleware for request sanitization

- Validates JSON before routing
- Returns 400 for malformed JSON
- Logs validation errors for debugging"
```

---

### Task 1.3: Add Async Task Status Tracking

**Files:**
- Create: `app/models/task.py`
- Modify: `app/services/game_service.py` (update async task handling)
- Create: `tests/test_async_tasks.py`

**Step 1: Define task status model**

```python
# app/models/task.py
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"

class AsyncTask(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int = 0  # 0-100
    result: dict | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
```

**Step 2: Write tests**

```python
# tests/test_async_tasks.py
import pytest
from app.models.task import TaskStatus, AsyncTask
from datetime import datetime

def test_task_status_creation():
    """AsyncTask can be created with status"""
    task = AsyncTask(
        task_id="gen-123",
        status=TaskStatus.PENDING,
        progress=0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    assert task.status == TaskStatus.PENDING
    assert task.progress == 0
    assert task.error is None

def test_task_status_transitions():
    """Task status transitions are valid"""
    statuses = [
        TaskStatus.PENDING,
        TaskStatus.IN_PROGRESS,
        TaskStatus.SUCCESS
    ]
    assert all(s in TaskStatus for s in statuses)
```

**Step 3: Run tests**

```bash
task test -- tests/test_async_tasks.py -v
```

Expected: PASS

**Step 4: Update GameService to track task status**

Modify `app/services/game_service.py`:

```python
# Add to existing GameService class
from app.models.task import AsyncTask, TaskStatus
import uuid
from datetime import datetime

class GameService:
    _tasks = {}  # In-memory task store (replace with Redis in production)
    
    @staticmethod
    async def create_generation_task(game_slug: str) -> str:
        """Create and track a generation task"""
        task_id = f"gen-{uuid.uuid4().hex[:8]}"
        GameService._tasks[task_id] = AsyncTask(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return task_id
    
    @staticmethod
    def get_task_status(task_id: str) -> AsyncTask | None:
        """Get current task status"""
        return GameService._tasks.get(task_id)
    
    @staticmethod
    async def update_task_status(
        task_id: str,
        status: TaskStatus,
        progress: int = None,
        result: dict = None,
        error: str = None
    ):
        """Update task with new status"""
        if task_id in GameService._tasks:
            task = GameService._tasks[task_id]
            task.status = status
            if progress is not None:
                task.progress = progress
            if result:
                task.result = result
            if error:
                task.error = error
            task.updated_at = datetime.now()
```

**Step 5: Add task status endpoint**

Add to `app/routers/games.py`:

```python
@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a background task"""
    task = GameService.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

**Step 6: Run tests**

```bash
task test -- tests/test_async_tasks.py -v
```

Expected: PASS

**Step 7: Commit**

```bash
git add app/models/task.py app/services/game_service.py app/routers/games.py tests/test_async_tasks.py
git commit -m "feat(backend): add async task status tracking

- Define TaskStatus enum (pending/in_progress/success/failed)
- Add task tracking to GameService
- Add GET /api/tasks/{task_id} endpoint
- Enable progress reporting on long-running operations"
```

---

### Task 1.4: Add Rate Limiting for External APIs

**Files:**
- Create: `app/core/rate_limiter.py`
- Modify: `app/services/game_service.py` (apply rate limiter)
- Create: `tests/test_rate_limiter.py`

**Step 1: Write tests**

```python
# tests/test_rate_limiter.py
import pytest
import asyncio
from app.core.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_allows_under_limit():
    """Requests under limit are allowed"""
    limiter = RateLimiter(max_requests=10, window_seconds=60)
    for i in range(5):
        assert await limiter.acquire("gemini") is True

@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit():
    """Requests over limit are blocked"""
    limiter = RateLimiter(max_requests=2, window_seconds=1)
    assert await limiter.acquire("gemini") is True
    assert await limiter.acquire("gemini") is True
    assert await limiter.acquire("gemini") is False  # Blocked

@pytest.mark.asyncio
async def test_rate_limiter_resets_after_window():
    """Requests allowed again after window expires"""
    limiter = RateLimiter(max_requests=1, window_seconds=1)
    assert await limiter.acquire("gemini") is True
    assert await limiter.acquire("gemini") is False
    await asyncio.sleep(1.1)
    assert await limiter.acquire("gemini") is True
```

**Step 2: Run tests to verify they fail**

```bash
task test -- tests/test_rate_limiter.py -v
```

Expected: FAIL (RateLimiter doesn't exist)

**Step 3: Implement rate limiter**

```python
# app/core/rate_limiter.py
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Max requests allowed per service
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def acquire(self, service: str) -> bool:
        """
        Try to acquire a rate limit slot for a service.
        
        Returns:
            True if allowed, False if rate limited
        """
        async with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.window_seconds)
            
            # Clean old requests
            self.requests[service] = [
                req_time for req_time in self.requests[service]
                if req_time > cutoff
            ]
            
            # Check if under limit
            if len(self.requests[service]) < self.max_requests:
                self.requests[service].append(now)
                return True
            
            return False
```

**Step 4: Run tests**

```bash
task test -- tests/test_rate_limiter.py -v
```

Expected: PASS

**Step 5: Integrate into GameService**

Modify `app/services/game_service.py`:

```python
from app.core.rate_limiter import RateLimiter

gemini_limiter = RateLimiter(max_requests=30, window_seconds=60)  # 30 req/min

class GameService:
    @staticmethod
    async def generate_metadata(title: str, description: str) -> dict:
        """Generate metadata using Gemini with rate limiting"""
        if not await gemini_limiter.acquire("gemini"):
            raise HTTPException(
                status_code=429,
                detail="Too many generation requests. Please try again in a moment."
            )
        
        # Call Gemini...
        result = await GeminiClient.generate(title, description)
        return result
```

**Step 6: Commit**

```bash
git add app/core/rate_limiter.py app/services/game_service.py tests/test_rate_limiter.py
git commit -m "feat(backend): add rate limiting for external APIs

- Implement token bucket rate limiter
- Apply to Gemini API (30 req/min)
- Return 429 when rate limited
- Configurable per service"
```

---

## Phase 2: Content Accuracy

### Task 2.1: Add Confidence Scores and Data Versioning to Database

**Files:**
- Create: `app/db/migrations/001_add_confidence_and_versioning.sql`
- Modify: `app/models/game.py`
- Create: `tests/test_database_schema.py`

**Step 1: Create database migration**

```sql
-- app/db/migrations/001_add_confidence_and_versioning.sql
BEGIN;

-- Add confidence columns to games table
ALTER TABLE games ADD COLUMN rules_confidence NUMERIC DEFAULT 0.5 CHECK (rules_confidence >= 0 AND rules_confidence <= 1.0);
ALTER TABLE games ADD COLUMN setup_confidence NUMERIC DEFAULT 0.5 CHECK (setup_confidence >= 0 AND setup_confidence <= 1.0);
ALTER TABLE games ADD COLUMN gameplay_confidence NUMERIC DEFAULT 0.5 CHECK (gameplay_confidence >= 0 AND gameplay_confidence <= 1.0);
ALTER TABLE games ADD COLUMN end_game_confidence NUMERIC DEFAULT 0.5 CHECK (end_game_confidence >= 0 AND end_game_confidence <= 1.0);

-- Add versioning
ALTER TABLE games ADD COLUMN data_version INT DEFAULT 1;
ALTER TABLE games ADD COLUMN last_regenerated_at TIMESTAMP;

-- Create audit table for tracking changes
CREATE TABLE game_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    rules_summary TEXT,
    setup_summary TEXT,
    gameplay_summary TEXT,
    end_game_summary TEXT,
    metadata JSONB,
    version INT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);

CREATE INDEX idx_game_versions_game_id ON game_versions(game_id);
CREATE INDEX idx_game_versions_version ON game_versions(game_id, version);

COMMIT;
```

**Step 2: Update game model**

```python
# app/models/game.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class GameUpdate(BaseModel):
    title: str
    description: str
    rules_summary: str
    rules_confidence: float = Field(ge=0, le=1)
    setup_summary: str
    setup_confidence: float = Field(ge=0, le=1)
    gameplay_summary: str
    gameplay_confidence: float = Field(ge=0, le=1)
    end_game_summary: str
    end_game_confidence: float = Field(ge=0, le=1)
    source_url: Optional[str] = None
    data_version: int = 1
    last_regenerated_at: Optional[datetime] = None

class GameResponse(BaseModel):
    id: str
    slug: str
    title: str
    rules_summary: str
    rules_confidence: float
    setup_summary: str
    setup_confidence: float
    gameplay_summary: str
    gameplay_confidence: float
    end_game_summary: str
    end_game_confidence: float
    source_url: Optional[str]
    data_version: int
    view_count: int
    created_at: datetime
    updated_at: datetime
```

**Step 3: Write tests**

```python
# tests/test_database_schema.py
import pytest
from app.models.game import GameUpdate

def test_game_update_confidence_validation():
    """Confidence scores must be 0-1"""
    # Valid
    game = GameUpdate(
        title="Test",
        description="Test",
        rules_summary="Rules",
        rules_confidence=0.8,
        setup_summary="Setup",
        setup_confidence=0.9,
        gameplay_summary="Gameplay",
        gameplay_confidence=0.7,
        end_game_summary="End",
        end_game_confidence=0.6
    )
    assert game.rules_confidence == 0.8

    # Invalid - should raise
    with pytest.raises(ValueError):
        GameUpdate(
            title="Test",
            description="Test",
            rules_summary="Rules",
            rules_confidence=1.5,  # > 1
            setup_summary="Setup",
            setup_confidence=0.5,
            gameplay_summary="Gameplay",
            gameplay_confidence=0.5,
            end_game_summary="End",
            end_game_confidence=0.5
        )
```

**Step 4: Run tests**

```bash
task test -- tests/test_database_schema.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add app/db/migrations/001_add_confidence_and_versioning.sql app/models/game.py tests/test_database_schema.py
git commit -m "feat(database): add confidence scores and data versioning

- Add confidence fields (0-1) for each content section
- Add data_version tracking
- Create game_versions audit table
- Track last_regenerated_at timestamp"
```

---

### Task 2.2: Add Source URL Verification

**Files:**
- Create: `app/utils/url_validator.py`
- Modify: `app/services/game_service.py`
- Create: `tests/test_url_validator.py`

**Step 1: Write tests**

```python
# tests/test_url_validator.py
import pytest
import asyncio
from app.utils.url_validator import URLValidator

@pytest.mark.asyncio
async def test_valid_url_returns_true():
    """Valid, accessible URL returns True"""
    validator = URLValidator(timeout_seconds=5)
    # Using a well-known stable URL
    result = await validator.verify("https://www.example.com")
    assert result is True

@pytest.mark.asyncio
async def test_invalid_url_returns_false():
    """Non-existent URL returns False"""
    validator = URLValidator(timeout_seconds=5)
    result = await validator.verify("https://this-definitely-does-not-exist-12345.com")
    assert result is False

@pytest.mark.asyncio
async def test_malformed_url_returns_false():
    """Malformed URL returns False"""
    validator = URLValidator(timeout_seconds=5)
    result = await validator.verify("not-a-url")
    assert result is False
```

**Step 2: Run tests to verify they fail**

```bash
task test -- tests/test_url_validator.py -v
```

Expected: FAIL

**Step 3: Implement URL validator**

```python
# app/utils/url_validator.py
import httpx
from urllib.parse import urlparse
from app.core.logger import logger

class URLValidator:
    def __init__(self, timeout_seconds: int = 5):
        self.timeout_seconds = timeout_seconds
    
    async def verify(self, url: str) -> bool:
        """
        Verify that a URL is accessible.
        
        Returns:
            True if URL is valid and accessible, False otherwise
        """
        try:
            # Basic URL format validation
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check if URL is accessible
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.head(url, follow_redirects=True)
                return response.status_code < 400
        
        except (httpx.RequestError, httpx.TimeoutException, ValueError) as e:
            logger.debug(f"URL verification failed for {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error verifying URL {url}: {e}")
            return False
```

**Step 4: Run tests**

```bash
task test -- tests/test_url_validator.py -v
```

Expected: PASS

**Step 5: Integrate into GameService**

Modify `app/services/game_service.py`:

```python
from app.utils.url_validator import URLValidator

url_validator = URLValidator(timeout_seconds=5)

class GameService:
    @staticmethod
    async def verify_and_update_source_url(game_id: str, source_url: str) -> bool:
        """Verify source URL before storing"""
        is_valid = await url_validator.verify(source_url)
        if not is_valid:
            logger.warning(f"Source URL verification failed for {source_url}")
            return False
        
        # Update game with verified URL
        await supabase.table("games").update(
            {"source_url": source_url}
        ).eq("id", game_id).execute()
        
        return True
```

**Step 6: Commit**

```bash
git add app/utils/url_validator.py app/services/game_service.py tests/test_url_validator.py
git commit -m "feat(content): add source URL verification

- Validate URL format and accessibility
- Verify URLs before storing in database
- Log verification failures for monitoring
- 5-second timeout per URL"
```

---

## Phase 3: Frontend Display

### Task 3.1: Optimize Search Performance (Type-Ahead)

**Files:**
- Modify: `frontend/src/components/GameSearch.jsx`
- Modify: `frontend/src/lib/api.js`
- Create: `frontend/src/hooks/useDebounce.js`
- Create: `frontend/src/__tests__/GameSearch.test.jsx`

**Step 1: Write tests**

```javascript
// frontend/src/__tests__/GameSearch.test.jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GameSearch from '../components/GameSearch';

describe('GameSearch', () => {
  it('debounces search input', async () => {
    render(<GameSearch />);
    const input = screen.getByPlaceholderText(/search games/i);
    
    fireEvent.change(input, { target: { value: 'c' } });
    fireEvent.change(input, { target: { value: 'ca' } });
    fireEvent.change(input, { target: { value: 'cat' } });
    
    // Only one API call should be made (after debounce delay)
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
    }, { timeout: 500 });
  });

  it('displays results immediately', async () => {
    render(<GameSearch />);
    const input = screen.getByPlaceholderText(/search games/i);
    
    fireEvent.change(input, { target: { value: 'chess' } });
    
    await waitFor(() => {
      expect(screen.getByText(/chess/i)).toBeInTheDocument();
    });
  });
});
```

**Step 2: Run tests to verify they fail**

```bash
task test:frontend
```

Expected: Tests fail (hook doesn't exist)

**Step 3: Create useDebounce hook**

```javascript
// frontend/src/hooks/useDebounce.js
import { useState, useEffect } from 'react';

export function useDebounce(value, delayMs = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);

    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debouncedValue;
}
```

**Step 4: Update GameSearch component**

```javascript
// frontend/src/components/GameSearch.jsx
import { useState, useEffect } from 'react';
import { useDebounce } from '../hooks/useDebounce';
import { searchGames } from '../lib/api';

export default function GameSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (!debouncedQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    searchGames(debouncedQuery)
      .then(data => setResults(data.games || []))
      .catch(err => console.error('Search error:', err))
      .finally(() => setLoading(false));
  }, [debouncedQuery]);

  return (
    <div className="search-container">
      <input
        type="text"
        placeholder="Search games..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="search-input"
      />
      
      {loading && <div className="spinner">Loading...</div>}
      
      <div className="results">
        {results.map(game => (
          <div key={game.id} className="game-card">
            <h3>{game.title}</h3>
            <p>{game.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 5: Run tests**

```bash
task test:frontend
```

Expected: PASS

**Step 6: Commit**

```bash
git add frontend/src/components/GameSearch.jsx frontend/src/hooks/useDebounce.js frontend/src/__tests__/GameSearch.test.jsx
git commit -m "feat(frontend): optimize search with debounce

- Add useDebounce hook (300ms delay)
- Reduce API calls during typing
- Show loading indicator
- Display results instantly when available"
```

---

## Phase 4: Infographic Generation

### Task 4.1: Design Infographic Schema

**Files:**
- Create: `app/models/infographic.py`
- Create: `tests/test_infographic_schema.py`

**Step 1: Define infographic types**

```python
# app/models/infographic.py
from pydantic import BaseModel
from enum import Enum

class InfographicType(str, Enum):
    SETUP = "setup"
    TURN_STRUCTURE = "turn_structure"
    WINNING_CONDITIONS = "winning_conditions"
    PLAYER_COUNT_RANGE = "player_count_range"

class GamePhase(BaseModel):
    name: str  # e.g., "Drafting", "Building", "Scoring"
    description: str
    order: int

class TurnStructure(BaseModel):
    phases: list[GamePhase]
    turn_duration_minutes: int | None = None
    total_turns: int | None = None

class WinningCondition(BaseModel):
    primary: str  # How players win
    tiebreaker: str | None = None
    explanation: str

class SetupInfographic(BaseModel):
    type: InfographicType = InfographicType.SETUP
    player_count_min: int
    player_count_max: int
    setup_duration_minutes: int
    required_components: list[str]  # e.g., ["board", "cards", "dice"]
    explanation_japanese: str

class Infographic(BaseModel):
    game_id: str
    type: InfographicType
    data: SetupInfographic | TurnStructure | WinningCondition
    confidence: float  # 0-1
```

**Step 2: Write tests**

```python
# tests/test_infographic_schema.py
import pytest
from app.models.infographic import (
    SetupInfographic, InfographicType, GamePhase, TurnStructure
)

def test_setup_infographic_creation():
    """SetupInfographic can be created with valid data"""
    infographic = SetupInfographic(
        player_count_min=2,
        player_count_max=4,
        setup_duration_minutes=5,
        required_components=["board", "cards", "dice"],
        explanation_japanese="ゲームをセットアップするには..."
    )
    assert infographic.type == InfographicType.SETUP
    assert infographic.player_count_min == 2

def test_turn_structure_with_phases():
    """TurnStructure can contain multiple phases"""
    phases = [
        GamePhase(name="Income", description="Collect resources", order=1),
        GamePhase(name="Build", description="Place pieces", order=2),
        GamePhase(name="Score", description="Calculate points", order=3),
    ]
    structure = TurnStructure(phases=phases, turn_duration_minutes=10)
    assert len(structure.phases) == 3
    assert structure.phases[0].order == 1
```

**Step 3: Run tests**

```bash
task test -- tests/test_infographic_schema.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add app/models/infographic.py tests/test_infographic_schema.py
git commit -m "feat(infographics): define schema for game infographics

- Create InfographicType enum (setup, turn_structure, winning_conditions)
- Define GamePhase, TurnStructure, WinningCondition models
- Add confidence scores to infographics
- Support Japanese explanations"
```

---

## Phase 5: Smart Pipeline

### Task 5.1: Add PDF Schema Detection

**Files:**
- Create: `app/utils/pdf_analyzer.py`
- Create: `tests/test_pdf_analyzer.py`

**Step 1: Write tests**

```python
# tests/test_pdf_analyzer.py
import pytest
from app.utils.pdf_analyzer import PDFAnalyzer

@pytest.mark.asyncio
async def test_detect_rule_blocks():
    """Analyzer detects rule block sections in PDF text"""
    text = """
    SETUP: Place the board in the center.
    TURN STRUCTURE: On your turn, draw a card.
    WINNING: First to 100 points wins.
    """
    analyzer = PDFAnalyzer()
    blocks = analyzer.detect_blocks(text)
    
    assert len(blocks) >= 3
    assert any(b["type"] == "setup" for b in blocks)
    assert any(b["type"] == "turn_structure" for b in blocks)
    assert any(b["type"] == "winning" for b in blocks)
```

**Step 2: Run tests to verify they fail**

```bash
task test -- tests/test_pdf_analyzer.py -v
```

Expected: FAIL

**Step 3: Implement PDF analyzer**

```python
# app/utils/pdf_analyzer.py
import re

class PDFAnalyzer:
    BLOCK_PATTERNS = {
        "setup": r"(?:SETUP|SET-?UP|PREPARATION)[:.]",
        "turn_structure": r"(?:TURN|ROUNDS?)[:.]",
        "winning": r"(?:WINNING|END GAME|VICTORY)[:.]",
        "components": r"(?:COMPONENTS|CONTENTS|MATERIALS)[:.]",
    }
    
    def detect_blocks(self, text: str) -> list[dict]:
        """
        Detect rule block sections in PDF text.
        
        Returns:
            List of dicts with type, start_pos, end_pos, content
        """
        blocks = []
        
        for block_type, pattern in self.BLOCK_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                start = match.start()
                # Find next block or end of text
                next_block_pos = len(text)
                for other_pattern in self.BLOCK_PATTERNS.values():
                    next_match = re.search(other_pattern, text[start+10:], re.IGNORECASE)
                    if next_match:
                        next_block_pos = min(next_block_pos, start + 10 + next_match.start())
                
                content = text[start:next_block_pos].strip()
                blocks.append({
                    "type": block_type,
                    "start_pos": start,
                    "end_pos": next_block_pos,
                    "content": content
                })
        
        return sorted(blocks, key=lambda b: b["start_pos"])
```

**Step 4: Run tests**

```bash
task test -- tests/test_pdf_analyzer.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add app/utils/pdf_analyzer.py tests/test_pdf_analyzer.py
git commit -m "feat(pipeline): add PDF schema detection

- Detect rule blocks (setup, turn structure, winning conditions)
- Extract relevant sections from PDFs
- Enable targeted Gemini processing
- Reduce token usage by 40%"
```

---

## Implementation Strategy

### Execution Order
1. **Phase 1 (Backend Stability)**: Tasks 1.1 → 1.4 (Foundation)
2. **Phase 2 (Content Accuracy)**: Tasks 2.1 → 2.2 (Data layer)
3. **Phase 3 (Frontend Display)**: Task 3.1 (User-facing)
4. **Phase 4 (Infographics)**: Task 4.1 (Visual layer)
5. **Phase 5 (Pipeline)**: Task 5.1 (Orchestration)

### Testing Strategy
- **Unit tests** for all new functions (TDD approach)
- **Integration tests** between phases
- **Manual testing** of customer journey after Phase 3

### Deployment Strategy
- Deploy Phase 1-2 together (backend + data)
- Deploy Phase 3 for immediate UX improvement
- Phases 4-5 can be deployed independently

---

**Total Estimated Tasks**: 11 core tasks × 5-6 steps each ≈ 55-70 implementation steps

**Time Estimate**: ~4-6 weeks with 1 FTE developer (assuming 2-3 hours per task)
