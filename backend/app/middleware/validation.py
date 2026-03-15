import json
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("middleware.validation")


class ValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PATCH", "PUT"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                # Use request.body() directly but be aware it's cached in FastAPI's Request object
                # for subsequent use in dependency injection
                body = await request.body()
                if body:
                    try:
                        json.loads(body)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Malformed JSON in {request.url}: {e}")
                        return JSONResponse(status_code=400, content={"error": f"Invalid JSON: {e!s}"})

        return await call_next(request)
