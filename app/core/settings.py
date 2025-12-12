import os
from pathlib import Path
from dotenv import load_dotenv

import yaml


def load_config():
    config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


_config = load_config()

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY")
    gemini_model: str = _config.get("gemini_model", "gemini-2.5-flash-lite")
    supabase_url: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv(
        "SUPABASE_URL"
    )
    supabase_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv(
        "SUPABASE_KEY"
    )


settings = Settings()
