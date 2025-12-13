import pytest
import sys
from pathlib import Path
import asyncio

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.game_service import generate_metadata


@pytest.mark.asyncio
async def test_real_api_timeout_limit():
    """
    Integration Test:
    Verifies if the real Gemini API response time is within the Vercel 10s limit.
    This test connects to the REAL API.

    EXPECTED BEHAVIOR:
    - If execution > 10s, this test FAILS (TimeoutError).
    -This reflects the production issue where Vercel kills the process.
    """

    # Enforce 10s timeout (Vercel Limit)
    try:
        print("\nCalling Real Gemini API (Timeout Limit: 10s)...")
        # Python 3.10 compatible timeout
        result = await asyncio.wait_for(
            generate_metadata("Terraforming Mars"), timeout=10.0
        )
        assert result is not None
        print("Success within time limit.")

    except asyncio.TimeoutError:
        pytest.fail(
            "Test Failed: Operation timed out (>10s). This confirms the production issue."
        )
    except Exception as e:
        pytest.fail(f"Test Failed with Error: {e}")
