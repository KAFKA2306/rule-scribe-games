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

CANONICAL_GEMINI_MODEL = "models/gemini-3-flash-preview"


class Settings:
    def __init__(self) -> None:
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        requested_model = os.getenv("GEMINI_MODEL") or _config.get(
            "gemini_model", CANONICAL_GEMINI_MODEL
        )
        if not requested_model.startswith("models/"):
            raise ValueError(
                "GEMINI_MODEL must include the `models/` prefix "
                "(example: models/gemini-3-flash-preview)."
            )
        if requested_model != CANONICAL_GEMINI_MODEL:
            raise ValueError(
                f"GEMINI_MODEL must be exactly `{CANONICAL_GEMINI_MODEL}` "
                f"(got `{requested_model}`)."
            )

        self.gemini_model = requested_model

        self.supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv(
            "SUPABASE_URL"
        )
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv(
            "SUPABASE_KEY"
        )


settings = Settings()
