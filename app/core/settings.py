import os

from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root (3 levels up: core -> app -> root)
try:
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(env_path)
except Exception:
    pass  # In Vercel, env vars are injected directly

PLACEHOLDER = "PLACEHOLDER"


def _env(name: str) -> str:
    return os.getenv(name, PLACEHOLDER)


class Settings:
    gemini_api_key: str = _env("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    supabase_url: str = (
        os.getenv("NEXT_PUBLIC_SUPABASE_URL")  # Shared with frontend
        or os.getenv("SUPABASE_URL")  # Vercel integration default
        or PLACEHOLDER
    )
    supabase_key: str = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Explicit write access
        or os.getenv("SUPABASE_KEY")  # Fallback
        or PLACEHOLDER
    )


settings = Settings()
