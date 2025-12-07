from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import games
from app.core.logger import setup_logging
from app.core.gemini import RateLimitError

setup_logging()

app = FastAPI(title="RuleScribe Minimal", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(games.router, prefix="/api", tags=["games"])


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError):
    return JSONResponse(status_code=429, content={"detail": "rate_limit"})


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok"}
