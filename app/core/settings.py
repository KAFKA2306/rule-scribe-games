import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

PLACEHOLDER = "PLACEHOLDER"


class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", PLACEHOLDER)
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    supabase_url: str = (
        os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        or os.getenv("SUPABASE_URL")
        or PLACEHOLDER
    )
    supabase_key: str = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or PLACEHOLDER
    )


settings = Settings()
