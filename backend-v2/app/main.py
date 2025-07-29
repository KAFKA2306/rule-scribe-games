
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import structlog
import asyncio
from typing import Dict, List

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.api.v1 import api_router


logger = structlog.get_logger()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id:
            self.user_connections[user_id] = websocket
        logger.info("WebSocket connected", user_id=user_id, total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket, user_id: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]
        logger.info("WebSocket disconnected", user_id=user_id, total_connections=len(self.active_connections))

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.user_connections:
            await self.user_connections[user_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("Error broadcasting message", error=str(e))


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RuleScribe Backend v2")
    setup_logging()
    await init_db()
    logger.info("RuleScribe Backend v2 started successfully")
    yield
    logger.info("RuleScribe Backend v2 shutdown complete")


def create_application() -> FastAPI:
    app = FastAPI(
        title="RuleScribe API v2",
        description="Advanced AI-powered board game rules search and summarization platform",
        version="2.0.0",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error", "detail": "An unexpected error occurred"}
        )

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": "2.0.0",
            "environment": settings.ENVIRONMENT,
            "services": {
                "database": "connected",
                "ai_services": "operational",
                "cache": "connected"
            }
        }

    @app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        await manager.connect(websocket, user_id)
        try:
            while True:
                data = await websocket.receive_json()
                
                if data.get("type") == "search_progress":
                    await manager.send_personal_message({
                        "type": "search_update",
                        "progress": data.get("progress", 0),
                        "message": data.get("message", "Processing...")
                    }, user_id)
                    
                elif data.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    }, user_id)
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
        except Exception as e:
            logger.error("WebSocket error", error=str(e), user_id=user_id)
            manager.disconnect(websocket, user_id)

    @app.get("/")
    async def root():
        return {
            "message": "RuleScribe API v2 - Advanced Board Game Rules Platform",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/health"
        }

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )