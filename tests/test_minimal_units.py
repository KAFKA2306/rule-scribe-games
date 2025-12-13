import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import units to test
from app.core.gemini import GeminiClient
from app.services.game_service import generate_metadata, _merge_fields

# ==========================================
# Unit 1: Gemini Client Parsing (Crash Only)
# ==========================================


@pytest.mark.asyncio
async def test_gemini_client_success():
    """Test that GeminiClient correctly parses a standard JSON response."""
    mock_response_data = {
        "candidates": [{"content": {"parts": [{"text": '{"title": "Test Game"}'}]}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Response object itself should be a MagicMock (sync methods like .json())
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None

        # The await client.post(...) returns this response
        mock_post.return_value = mock_response

        client = GeminiClient()
        result = await client.generate_structured_json("prompt")

        assert result == {"title": "Test Game"}


@pytest.mark.asyncio
async def test_gemini_client_crash_on_invalid_json():
    """Test that GeminiClient crashes (raises JSONDecodeError) if response is not JSON."""
    mock_response_data = {
        "candidates": [{"content": {"parts": [{"text": "I am not JSON"}]}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None

        mock_post.return_value = mock_response

        client = GeminiClient()

        # Expect crash
        with pytest.raises(json.JSONDecodeError):
            await client.generate_structured_json("prompt")


# ==========================================
# Unit 2: Metadata Logic (Date/URL Augmentation)
# ==========================================


@pytest.mark.asyncio
async def test_generate_metadata_augmentation():
    """Test that generated metadata is augmented with updated_at and amazon_url."""
    from urllib.parse import quote

    mock_gemini_return = {"title": "Catan", "title_ja": "カタン"}

    with patch(
        "app.services.game_service._gemini.generate_structured_json",
        new_callable=AsyncMock,
    ) as mock_gen:
        with patch(
            "app.services.game_service.supabase.search", new_callable=AsyncMock
        ) as mock_search:
            mock_gen.return_value = mock_gemini_return
            mock_search.return_value = []  # No context

            result = await generate_metadata("Catan")

            assert result["title"] == "Catan"
            assert "updated_at" in result
            assert "amazon_url" in result
            # Check for encoded string in URL
            assert quote("カタン") in result["amazon_url"]


# ==========================================
# Unit 3: Data Merging Logic
# ==========================================


def test_merge_fields_overwrite():
    """Test that _merge_fields overwrites data when fill_missing_only=False."""
    original = {"title": "Old", "desc": "Keep"}
    incoming = {"title": "New"}

    result = _merge_fields(original, incoming, fill_missing_only=False)
    assert result["title"] == "New"
    assert result["desc"] == "Keep"


def test_merge_fields_fill_missing():
    """Test that _merge_fields only fills missing/empty fields when fill_missing_only=True."""
    original = {"title": "Old", "desc": "", "empty": None}
    incoming = {"title": "New", "desc": "Filled", "empty": "Filled"}

    result = _merge_fields(original, incoming, fill_missing_only=True)
    assert result["title"] == "Old"  # Should NOT change
    assert result["desc"] == "Filled"  # Should change (empty string)
    assert result["empty"] == "Filled"  # Should change (None)
