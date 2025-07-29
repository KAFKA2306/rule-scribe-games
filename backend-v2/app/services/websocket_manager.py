"""
WebSocket connection manager for real-time features
"""

from typing import Dict, List
from fastapi import WebSocket
import structlog
import json
import time

logger = structlog.get_logger()


class WebSocketManager:
    """Manage WebSocket connections and messaging"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Connect a new WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id:
            self.user_connections[user_id] = websocket
        
        logger.info("WebSocket connected", 
                   user_id=user_id, 
                   total_connections=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """Disconnect a WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]
        
        logger.info("WebSocket disconnected", 
                   user_id=user_id, 
                   total_connections=len(self.active_connections))
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_text(json.dumps(message))
                logger.debug("Personal message sent", user_id=user_id)
            except Exception as e:
                logger.error("Failed to send personal message", 
                           user_id=user_id, error=str(e))
                # Remove failed connection
                self.disconnect(self.user_connections[user_id], user_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        if not self.active_connections:
            return
        
        disconnected = []
        message_str = json.dumps(message)
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error("Failed to broadcast message", error=str(e))
                disconnected.append(connection)
        
        # Clean up failed connections
        for connection in disconnected:
            self.disconnect(connection)
        
        logger.info("Message broadcasted", 
                   recipients=len(self.active_connections) - len(disconnected))
    
    async def send_search_progress(self, user_id: str, progress: int, message: str):
        """Send search progress update to user"""
        await self.send_personal_message({
            "type": "search_progress",
            "progress": progress,
            "message": message,
            "timestamp": time.time()
        }, user_id)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def get_user_connection_count(self) -> int:
        """Get number of identified user connections"""
        return len(self.user_connections)