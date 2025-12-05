import os

PLACEHOLDER = "PLACEHOLDER"


def _env(name: str) -> str:
    return os.getenv(name, PLACEHOLDER)


class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "AIzaSyAdKr9zu4fgTwfdx1HcfpneX-Z51J9RbHs")
    gemini_model: str = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    supabase_url: str = (
        os.getenv("SUPABASE_URL")
        or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        or "https://wazgoplarevypdfbgeau.supabase.co"
    )
    supabase_key: str = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        or os.getenv("VITE_SUPABASE_ANON_KEY")
        or "sb_secret_ef8EjDpp4ynuPE3O7va04A_0RtugkRZ"
    )


settings = Settings()
