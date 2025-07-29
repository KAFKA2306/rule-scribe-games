"""
Simple backend test without AI dependencies
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

logger = structlog.get_logger()

def create_test_app():
    """Create a minimal test app"""
    app = FastAPI(
        title="RuleScribe API v2 - Test",
        description="Test version without external dependencies",
        version="2.0.0-test"
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
            "message": "RuleScribe API v2 - Test Mode",
            "version": "2.0.0-test",
            "status": "operational"
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "services": {
                "api": "operational",
                "test_mode": True
            }
        }
    
    @app.get("/api/v1/search/")
    async def search():
        return {
            "results": [
                {
                    "id": 1,
                    "title": "カタン",
                    "description": "島の開拓と資源管理の戦略ゲーム",
                    "rating": 4.5
                }
            ],
            "total": 1,
            "message": "Test search results"
        }
    
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_test_app()
    print("✅ Test backend created successfully")
    uvicorn.run(app, host="0.0.0.0", port=8000)