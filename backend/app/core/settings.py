import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def load_config() -> dict[str, Any]:
    # Use absolute path based on Vercel environment or current file
    root = Path(os.getenv("LAMBDA_TASK_ROOT", Path(__file__).resolve().parent.parent.parent.parent))
    possible_paths = [
        root / "config.yaml",
        root / "backend" / "config.yaml",
    ]
    for config_path in possible_paths:
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
    return {}


_config = load_config()
# Load .env from root
_root = Path(os.getenv("LAMBDA_TASK_ROOT", Path(__file__).resolve().parent.parent.parent.parent))
load_dotenv(_root / ".env")

CANONICAL_GEMINI_MODEL = "gemini-2.5-flash"


class Settings:
    def __init__(self) -> None:
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or str(_config.get("gemini_api_key") or "")
        self.gemini_model = os.getenv("GEMINI_MODEL") or str(_config.get("gemini_model") or CANONICAL_GEMINI_MODEL)
        self.supabase_url = (
            os.getenv("SUPABASE_URL") or
            os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        )
        self.supabase_key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY") or
            os.getenv("SUPABASE_ANON_KEY") or
            os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        )


settings = Settings()
