from pathlib import Path
from typing import Any, Dict

from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings
import yaml


def load_config() -> Dict[str, Any]:
    """
    Load config.yaml relative to the backend root to avoid import-time
    FileNotFoundError when the working directory is different.
    """
    root = Path(__file__).resolve().parents[2]  # backend/
    cfg_path = root / "config.yaml"
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()


PLACEHOLDER = "PLACEHOLDER"


class Settings(BaseSettings):
    # Provide safe defaults so the API can boot in "mock" mode when env vars are
    # not configured (e.g., preview deployments or local runs without secrets).
    gemini_api_key: str = Field(
        PLACEHOLDER, validation_alias=AliasChoices("GEMINI_API_KEY")
    )
    gemini_model: str = config.get("gemini", {}).get("model", "gemini-2.5-flash")

    supabase_url: str = Field(
        PLACEHOLDER, validation_alias=AliasChoices("SUPABASE_URL")
    )
    supabase_key: str = Field(
        PLACEHOLDER,
        validation_alias=AliasChoices("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY"),
    )

    class Config:
        env_file = Path(__file__).resolve().parents[2] / ".env"
        extra = "ignore"


settings = Settings()
