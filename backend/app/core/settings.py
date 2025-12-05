import os

from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root (3 levels up: core -> app -> backend -> root)
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(env_path)

PLACEHOLDER = "PLACEHOLDER"


def _env(name: str) -> str:
    return os.getenv(name, PLACEHOLDER)


class Settings:
    gemini_api_key: str = _env("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    supabase_url: str = (
        os.getenv("NEXT_PUBLIC_SUPABASE_URL")  # Shared with frontend
        or os.getenv("SUPABASE_URL")
        or PLACEHOLDER
    )
    supabase_key: str = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Explicit write access
        or os.getenv("SUPABASE_KEY")            # Fallback
        or PLACEHOLDER
    )


settings = Settings()
