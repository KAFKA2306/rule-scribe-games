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

@app.get("/api/debug/env")
async def debug_env():
    import os
    from app.core.gemini import GeminiClient
    
    gemini_works = False
    gemini_error = None
    try:
        client = GeminiClient()
        # Direct generation test
        await client.generate_structured_json("Return strictly valid JSON: {\"test\": \"ok\"}")
        gemini_works = True
    except Exception as e:
        gemini_error = str(e)

    return {
        "gemini_key_present": bool(os.getenv("GEMINI_API_KEY")),
        "supabase_url_present": bool(os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")),
        "supabase_key_present": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")),
        "gemini_test_success": gemini_works,
        "gemini_error": gemini_error
    }
