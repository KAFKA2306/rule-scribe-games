"""
Rate limiting functionality
"""

import time
from typing import Dict
import structlog
from fastapi import HTTPException

logger = structlog.get_logger()


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    async def check_rate_limit(self, identifier: str):
        """Check if request is within rate limit"""
        current_time = time.time()
        
        # Initialize if first request
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            logger.warning("Rate limit exceeded", identifier=identifier)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add current request
        self.requests[identifier].append(current_time)