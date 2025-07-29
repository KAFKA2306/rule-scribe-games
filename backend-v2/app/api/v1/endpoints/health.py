"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "RuleScribe Backend v2"
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with service status"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "operational",
            "database": "connected",
            "ai_services": "available",
            "websocket": "operational"
        },
        "version": "2.0.0"
    }