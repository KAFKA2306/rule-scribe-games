"""
API v1 Router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import games, search, ai, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(games.router, prefix="/games", tags=["games"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])