import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.game_service import generate_metadata

# This module intentionally contains breaker scenarios; mark as expected failures
pytestmark = pytest.mark.xfail(
    reason="Intentional failure tests; do not fail CI when they trigger",
    strict=False,
)


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="System is designed to be slow/crash-only")
async def test_failure_performance_limit():
    """
    FAILURE TEST 1: Performance
    Asserts that the operation completes in < 5 seconds.
    EXPECTED TO FAIL: Actual execution is > 9s.
    """
    print("\nRunning Failing Test 1: Performance < 5s...")
    try:
        # Enforce 5s limit
        await asyncio.wait_for(generate_metadata("Terraforming Mars"), timeout=5.0)
    except asyncio.TimeoutError:
        pytest.fail(
            "STRICT FAILURE: SYSTEM_TOO_SLOW. Execution > 5s. (Backend Timeout Risk)"
        )


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True, reason="System is designed to crash on 503 (Crash Only)"
)
async def test_failure_resilience_503():
    """
    FAILURE TEST 2: Resilience
    Asserts that a 503 error is caught and handled gracefully (no exception).
    EXPECTED TO FAIL: We removed exception handlers, so this will raise httpx.HTTPStatusError.
    """
    print("\nRunning Failing Test 2: Resilience 503 Handling...")

    # Mock Response object (Sync methods)
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "503 Service Unavailable", request=None, response=mock_response
    )

    # Mock Async Client
    with patch(
        "app.core.gemini.httpx.AsyncClient.post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = mock_response

        try:
            # We invite the crash
            await generate_metadata("Test")
        except httpx.HTTPStatusError:
            pytest.fail(
                "STRICT FAILURE: CRASH_ON_503. System crashed instead of recovering. (Crash Only Mode)"
            )


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="System is designed to leak raw errors (Unsafe)")
async def test_failure_safety_no_raw_errors():
    """
    FAILURE TEST 3: Safety
    Asserts that we do NOT see a raw 500 error propagate (Crash Only).
    EXPECTED TO FAIL: We removed the global exception handler, so raw errors propagate.
    """
    print("\nRunning Failing Test 3: Safety No Raw Errors...")

    # Mock Response object (Sync methods)
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Internal Server Error", request=None, response=mock_response
    )

    with patch(
        "app.core.gemini.httpx.AsyncClient.post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = mock_response

        try:
            await generate_metadata("Test")
        except Exception:
            # If we catch it here, it means it propagated out of the app logic
            pytest.fail(
                "STRICT FAILURE: RAW_EXCEPTION_LEAK. 500 Error propagated to user. (Unsafe)"
            )
