from pathlib import Path

# Make python-dotenv optional in serverless environments.
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - Vercel may not install optional deps
    def load_dotenv(*args, **kwargs):
        return False

# Load .env from repository root (fallback to backend/.env if needed).
repo_root_env = Path(__file__).resolve().parents[2] / ".env"
backend_env = Path(__file__).resolve().parents[1] / ".env"
if repo_root_env.exists():
    load_dotenv(dotenv_path=repo_root_env, override=True)
elif backend_env.exists():
    load_dotenv(dotenv_path=backend_env, override=True)
else:
    load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import search, summarize
from app.core.settings import settings

app = FastAPI(title="RuleScribe Minimal", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # relax origin but keep credentials off to avoid startup error
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(summarize.router, prefix="/api", tags=["summarize"])


@app.get("/health")
@app.get("/api/health")
def health_check():
    env_report = {
        "gemini_api_key_present": settings.gemini_api_key not in ("", "PLACEHOLDER", None),
        "supabase_url_present": settings.supabase_url not in ("", "PLACEHOLDER", None),
        "supabase_service_role_present": settings.supabase_key not in ("", "PLACEHOLDER", None),
    }
    return {"status": "ok", "env": env_report}
