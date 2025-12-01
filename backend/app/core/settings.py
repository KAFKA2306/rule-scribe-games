import os

def _env(name: str) -> str:
    return os.getenv(name, "")


class Settings:
    gemini_api_key: str = _env("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    supabase_url: str = _env("SUPABASE_URL")
    supabase_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or _env("SUPABASE_KEY")


settings = Settings()
