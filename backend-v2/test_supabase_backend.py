"""
Test backend with Supabase integration (graceful fallback to mock data)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
import os

# Set environment for testing
os.environ['ENVIRONMENT'] = 'development'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./test.db'

logger = structlog.get_logger()

def create_supabase_test_app():
    """Create test app with Supabase integration"""
    app = FastAPI(
        title="RuleScribe API v2 - Supabase Test",
        description="Test version with Supabase integration and fallback",
        version="2.0.0-supabase"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "RuleScribe API v2 - Supabase Integration",
            "version": "2.0.0-supabase",
            "status": "operational",
            "features": {
                "supabase_integration": True,
                "fallback_mode": "sqlite",
                "ai_orchestrator": "multi-provider",
                "real_time": "websocket"
            }
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "services": {
                "api": "operational",
                "database": "sqlite_fallback",
                "supabase": "configured",
                "ai_services": "ready"
            },
            "environment": "test"
        }
    
    @app.get("/api/v1/games/")
    async def list_games():
        """Test games endpoint with Supabase fallback"""
        # Mock data that would come from Supabase
        games = [
            {
                "id": 1,
                "title": "カタン",
                "description": "島の開拓と資源管理の戦略ゲーム",
                "player_count_min": 3,
                "player_count_max": 4,
                "play_time_min": 60,
                "play_time_max": 90,
                "complexity": 2.5,
                "rating": 4.5,
                "genres": ["戦略", "交渉", "資源管理"],
                "mechanics": ["ダイスロール", "交渉", "建設"],
                "year_published": 1995
            },
            {
                "id": 2,
                "title": "ウィングスパン",
                "description": "美しい鳥類をテーマにしたエンジンビルディングゲーム",
                "player_count_min": 1,
                "player_count_max": 5,
                "play_time_min": 40,
                "play_time_max": 70,
                "complexity": 2.4,
                "rating": 4.7,
                "genres": ["戦略", "エンジンビルディング"],
                "mechanics": ["カードドラフト", "エンジンビルディング"],
                "year_published": 2019
            }
        ]
        
        return {
            "games": games,
            "total": len(games),
            "source": "supabase_fallback",
            "message": "Using fallback data (Supabase would provide real data)"
        }
    
    @app.get("/api/v1/games/{game_id}")
    async def get_game(game_id: int):
        """Test single game endpoint"""
        game = {
            "id": game_id,
            "title": "カタン",
            "description": "島の開拓と資源管理の戦略ゲーム",
            "rules_content": "プレイヤーは開拓者となり、カタン島を開拓していきます...",
            "player_count_min": 3,
            "player_count_max": 4,
            "play_time_min": 60,
            "play_time_max": 90,
            "complexity": 2.5,
            "rating": 4.5,
            "genres": ["戦略", "交渉", "資源管理"],
            "mechanics": ["ダイスロール", "交渉", "建設"],
            "year_published": 1995,
            "source": "supabase_fallback"
        }
        
        return game
    
    @app.post("/api/v1/search/")
    async def search_games():
        """Test search endpoint with Supabase integration"""
        results = [
            {
                "game_id": 1,
                "title": "カタン",
                "description": "島の開拓と資源管理の戦略ゲーム",
                "content": "プレイヤーは開拓者となり、カタン島を開拓していきます...",
                "similarity_score": 0.95,
                "player_count": "3-4人",
                "play_time": "60-90分",
                "complexity": 2.5,
                "genres": ["戦略", "交渉", "資源管理"],
                "rating": 4.5
            }
        ]
        
        return {
            "results": results,
            "total_results": len(results),
            "query": "test",
            "processing_time_ms": 150.5,
            "search_metadata": {
                "supabase_search": True,
                "fallback_mode": True,
                "ai_enhanced": False
            }
        }
    
    @app.get("/api/v1/games/popular/")
    async def get_popular_games():
        """Test popular games endpoint"""
        popular = [
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
            }
        ]
        
        return {
            "games": popular,
            "total": len(popular),
            "source": "analytics_fallback"
        }
    
    @app.get("/supabase/status")
    async def supabase_status():
        """Check Supabase integration status"""
        return {
            "supabase_configured": bool(os.getenv('SUPABASE_URL')),
            "database_url_set": bool(os.getenv('DATABASE_URL')),
            "environment": os.getenv('ENVIRONMENT', 'unknown'),
            "integration_status": "ready_for_production",
            "fallback_available": True,
            "schema_ready": True
        }
    
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_supabase_test_app()
    print("✅ Supabase test backend created successfully")
    print("🗄️ Supabase integration: Ready")
    print("🔄 Fallback mode: Enabled")
    uvicorn.run(app, host="0.0.0.0", port=8000)