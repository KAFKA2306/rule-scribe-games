from pathlib import Path
import sys
import os

# --- Vercel Import Hack ---
# Vercel's Python runtime puts the handler file in a specific location.
# We need to ensure the `backend` directory is in sys.path so that `from app...` works.
# If `backend/app/main.py` is the entry point, then `backend` is the parent directory.

BASE_DIR = Path(__file__).resolve().parent.parent  # .../backend
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Also add the project root if needed (for finding .env or other resources)
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# --- Environment Loading ---
try:
    from dotenv import load_dotenv
    # Try loading .env from root first, then backend
    if (ROOT_DIR / ".env").exists():
        load_dotenv(ROOT_DIR / ".env")
    elif (BASE_DIR / ".env").exists():
        load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass # Vercel handles env vars via dashboard

# --- App ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import search, summarize

app = FastAPI(title="RuleScribe Minimal", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, # Changed to True for better compatibility if credentials are added later
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(summarize.router, prefix="/api", tags=["summarize"])

@app.get("/health")
@app.get("/api/health")
def health_check():
    """
    Health check endpoint.
    Returns status and environment variable presence (safe bools).
    """
    from app.core.settings import settings
    # Re-import safely just in case

    return {
        "status": "ok",
        "env": {
            "gemini": "PLACEHOLDER" not in settings.gemini_api_key and bool(settings.gemini_api_key),
            "supabase_url": "PLACEHOLDER" not in settings.supabase_url and bool(settings.supabase_url),
        }
    }
