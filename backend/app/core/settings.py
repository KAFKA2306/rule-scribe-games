import os

PLACEHOLDER = "PLACEHOLDER"


def _env(name: str) -> str:
    return os.getenv(name, PLACEHOLDER)


class Settings:
    gemini_api_key: str = _env("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

    # Supabase URL: Try standard, then Vercel/Next.js integration standard
    supabase_url: str = (
        os.getenv("SUPABASE_URL")
        or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        or PLACEHOLDER
    )

    # Supabase Key: Try Service Role, then standard Key, then Anon Key (Vercel)
    supabase_key: str = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        or PLACEHOLDER
    )


settings = Settings()
