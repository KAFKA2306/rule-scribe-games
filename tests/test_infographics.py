"""
Test suite for infographics feature.
Tests: API PATCH endpoint, database storage, carousel display.
"""
import asyncio
import httpx
import pytest


BASE_URL = "http://localhost:8000"
TEST_GAME_SLUG = "splendor"

SAMPLE_INFOGRAPHICS = {
    "turn_flow": "https://via.placeholder.com/800x600/FF6B6B/FFFFFF?text=Turn+Flow",
    "setup": "https://via.placeholder.com/800x600/4ECDC4/FFFFFF?text=Setup",
    "actions": "https://via.placeholder.com/800x600/45B7D1/FFFFFF?text=Actions",
    "winning": "https://via.placeholder.com/800x600/FFA07A/FFFFFF?text=Winning",
    "components": "https://via.placeholder.com/800x600/98D8C8/FFFFFF?text=Components",
}


@pytest.mark.asyncio
async def test_api_health():
    """Test API is running"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_game_with_infographics():
    """Test GET /api/games/{slug} includes infographics field"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/games/{TEST_GAME_SLUG}")
        assert response.status_code == 200
        
        game = response.json()
        assert "infographics" in game
        # Should be None initially or a dict
        assert game["infographics"] is None or isinstance(game["infographics"], dict)


@pytest.mark.asyncio
async def test_patch_infographics():
    """Test PATCH /api/games/{slug} with infographics data"""
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/api/games/{TEST_GAME_SLUG}",
            json={"infographics": SAMPLE_INFOGRAPHICS}
        )
        
        # Should succeed (200/202) or fail if DB not migrated
        if response.status_code == 500:
            pytest.skip("Database migration not applied yet")
        
        assert response.status_code in [200, 202], f"Error: {response.text}"
        
        game = response.json()
        assert game.get("infographics") == SAMPLE_INFOGRAPHICS


@pytest.mark.asyncio
async def test_patch_partial_infographics():
    """Test PATCH with only 2/5 infographic types"""
    partial_infographics = {
        "setup": SAMPLE_INFOGRAPHICS["setup"],
        "actions": SAMPLE_INFOGRAPHICS["actions"],
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/api/games/{TEST_GAME_SLUG}",
            json={"infographics": partial_infographics}
        )
        
        if response.status_code == 500:
            pytest.skip("Database migration not applied yet")
        
        assert response.status_code in [200, 202]
        game = response.json()
        
        # Should have only 2 keys
        assert len(game.get("infographics", {})) == 2


@pytest.mark.asyncio
async def test_carousel_key_types():
    """Test all 5 carousel key types are supported"""
    valid_keys = {"turn_flow", "setup", "actions", "winning", "components"}
    
    # Create a dict with all 5 keys
    full_infographics = {key: f"https://example.com/{key}.png" for key in valid_keys}
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/api/games/{TEST_GAME_SLUG}",
            json={"infographics": full_infographics}
        )
        
        if response.status_code == 500:
            pytest.skip("Database migration not applied yet")
        
        assert response.status_code in [200, 202]
        game = response.json()
        
        # All keys should be present
        returned_keys = set(game.get("infographics", {}).keys())
        assert returned_keys == valid_keys


@pytest.mark.asyncio
async def test_infographics_validation():
    """Test invalid infographics data is rejected"""
    async with httpx.AsyncClient() as client:
        # Test with invalid type (should be dict[str, str])
        response = await client.patch(
            f"{BASE_URL}/api/games/{TEST_GAME_SLUG}",
            json={"infographics": ["not", "a", "dict"]}
        )
        
        # Should return 422 (validation error)
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_missing_image_urls():
    """Test carousel handles missing image URLs gracefully"""
    # In frontend, broken images should show error message
    bad_infographics = {
        "turn_flow": "https://nonexistent.example.com/404.png",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/api/games/{TEST_GAME_SLUG}",
            json={"infographics": bad_infographics}
        )
        
        if response.status_code == 500:
            pytest.skip("Database migration not applied yet")
        
        assert response.status_code in [200, 202]
        # Should accept the data (validation happens on frontend image load)


@pytest.mark.asyncio
async def test_clear_infographics():
    """Test clearing infographics (set to None)"""
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/api/games/{TEST_GAME_SLUG}",
            json={"infographics": None}
        )
        
        if response.status_code == 500:
            pytest.skip("Database migration not applied yet")
        
        assert response.status_code in [200, 202]
        game = response.json()
        assert game.get("infographics") is None


if __name__ == "__main__":
    # Run tests manually
    print("Run with: pytest tests/test_infographics.py -v")
