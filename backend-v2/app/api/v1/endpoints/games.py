"""
Games endpoints with Supabase integration
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import structlog
from app.services.supabase_service import supabase_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("/")
async def list_games(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List all games from Supabase"""
    try:
        games = await supabase_service.client.get_games(limit=limit, offset=offset)
        
        if not games:
            # Fallback to mock data if Supabase is unavailable
            games = [
                {
                    "id": 1,
                    "title": "カタン",
                    "description": "島の開拓と資源管理の戦略ゲーム",
                    "player_count_min": 3,
                    "player_count_max": 4,
                    "play_time_min": 60,
                    "play_time_max": 90,
                    "rating": 4.5,
                    "complexity": 2.5,
                    "genres": ["戦略", "交渉", "資源管理"]
                },
                {
                    "id": 2,
                    "title": "ウィングスパン",
                    "description": "美しい鳥類をテーマにしたエンジンビルディングゲーム",
                    "player_count_min": 1,
                    "player_count_max": 5,
                    "play_time_min": 40,
                    "play_time_max": 70,
                    "rating": 4.7,
                    "complexity": 2.4,
                    "genres": ["戦略", "エンジンビルディング"]
                }
            ]
        
        return {
            "games": games,
            "total": len(games),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Failed to list games", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve games")


@router.get("/{game_id}")
async def get_game(game_id: int):
    """Get specific game details from Supabase"""
    try:
        game = await supabase_service.get_game_details(game_id)
        
        if not game:
            # Fallback to mock data
            game = {
                "id": game_id,
                "title": "カタン",
                "description": "島の開拓と資源管理の戦略ゲーム",
                "rules_content": "詳細なルール説明がここに入ります...",
                "player_count_min": 3,
                "player_count_max": 4,
                "play_time_min": 60,
                "play_time_max": 90,
                "complexity": 2.5,
                "rating": 4.5,
                "genres": ["戦略", "交渉", "資源管理"],
                "mechanics": ["ダイスロール", "交渉", "建設"],
                "year_published": 1995
            }
        
        return game
        
    except Exception as e:
        logger.error("Failed to get game", game_id=game_id, error=str(e))
        raise HTTPException(status_code=404, detail="Game not found")


@router.get("/popular/")
async def get_popular_games(limit: int = Query(10, ge=1, le=50)):
    """Get popular games based on analytics"""
    try:
        popular_games = await supabase_service.get_popular_games(limit=limit)
        
        if not popular_games:
            # Fallback to featured games
            popular_games = [
                {
                    "id": 1,
                    "title": "カタン",
                    "description": "島の開拓と資源管理の戦略ゲーム",
                    "rating": 4.5,
                    "search_count": 1250
                },
                {
                    "id": 2,
                    "title": "ウィングスパン",
                    "description": "美しい鳥類をテーマにしたエンジンビルディングゲーム",
                    "rating": 4.7,
                    "search_count": 980
                },
                {
                    "id": 3,
                    "title": "アズール",
                    "description": "タイル配置の美しいアブストラクトゲーム",
                    "rating": 4.4,
                    "search_count": 850
                }
            ]
        
        return {
            "games": popular_games,
            "total": len(popular_games)
        }
        
    except Exception as e:
        logger.error("Failed to get popular games", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve popular games")


@router.post("/")
async def create_game(game_data: Dict[str, Any]):
    """Create new game in Supabase"""
    try:
        game_id = await supabase_service.store_game_rules(game_data)
        
        if not game_id:
            raise HTTPException(status_code=500, detail="Failed to create game")
        
        return {
            "message": "Game created successfully",
            "game_id": game_id
        }
        
    except Exception as e:
        logger.error("Failed to create game", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create game")


@router.put("/{game_id}")
async def update_game(game_id: int, updates: Dict[str, Any]):
    """Update existing game in Supabase"""
    try:
        success = await supabase_service.update_game_rules(game_id, updates)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update game")
        
        return {
            "message": "Game updated successfully",
            "game_id": game_id
        }
        
    except Exception as e:
        logger.error("Failed to update game", game_id=game_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update game")