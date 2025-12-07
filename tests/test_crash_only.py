import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.game_service import GameService

# raise_server_exceptions=False ensures 500 responses are returned instead of raising exceptions
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def mock_gemini():
    with patch("app.services.game_service._gemini") as mock:
        yield mock


@pytest.fixture
def mock_supabase():
    with patch("app.services.game_service.supabase") as mock:
        yield mock


@pytest.mark.asyncio
async def test_crash_on_gemini_error(mock_gemini, mock_supabase):
    """Verify that the API returns 500 when Gemini returns an error."""
    # Mock Gemini to return an error dict
    mock_gemini.generate_structured_json = AsyncMock(
        return_value={"error": "Rate limit exceeded"}
    )

    # Mock Supabase search to return something so we proceed to generation
    mock_supabase.search = AsyncMock(return_value=[])

    response = client.post("/api/search", json={"query": "test game", "generate": True})

    # Should be 500 because we raise RuntimeError
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_crash_on_validation_failure(mock_gemini, mock_supabase):
    """Verify that the API returns 500 when validation fails."""
    # Mock Gemini to return data missing required fields
    mock_gemini.generate_structured_json = AsyncMock(
        return_value={"data": {"title": "Test"}}
    )  # Missing summary, rules_content

    mock_supabase.search = AsyncMock(return_value=[])

    response = client.post("/api/search", json={"query": "test game", "generate": True})

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_synchronous_execution(mock_gemini, mock_supabase):
    """Verify that the API waits for the result (synchronous)."""
    # Mock successful generation
    mock_data = {
        "id": "123",
        "title": "Test Game",
        "summary": "A test game",
        "rules_content": "Rules here",
        "slug": "test-game",
    }
    mock_gemini.generate_structured_json = AsyncMock(return_value={"data": mock_data})
    mock_supabase.search = AsyncMock(return_value=[])
    mock_supabase.upsert = AsyncMock(return_value=[mock_data])

    response = client.post("/api/search", json={"query": "test game", "generate": True})

    assert response.status_code == 200
    assert response.json()[0]["slug"] == "test-game"

    # Verify upsert was called BEFORE response
    mock_supabase.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_patch_regenerate(mock_gemini, mock_supabase):
    """Verify PATCH /api/games/{slug}?regenerate=true returns updated game data."""
    # Mock existing game
    original_game = {
        "id": "123",
        "slug": "test-game",
        "title": "Test Game",
        "data_version": 1,
    }
    mock_supabase.get_by_slug = AsyncMock(return_value=original_game)

    # Mock generation result
    generated_data = {
        "title": "Test Game",
        "summary": "Updated summary",
        "rules_content": "Updated rules",
        "slug": "test-game",  # Should match
    }
    mock_gemini.generate_structured_json = AsyncMock(
        return_value={"data": generated_data}
    )

    # Mock upsert return
    updated_game = {**original_game, **generated_data, "data_version": 2}
    mock_supabase.upsert = AsyncMock(return_value=[updated_game])

    response = client.patch(
        "/api/games/test-game?regenerate=true&fill_missing_only=false"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "test-game"
    assert data["summary"] == "Updated summary"
    assert data["data_version"] == 2
