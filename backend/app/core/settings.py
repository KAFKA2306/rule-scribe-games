import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def load_config() -> dict[str, Any]:
    root = Path(os.getenv("LAMBDA_TASK_ROOT", Path(__file__).resolve().parent.parent.parent.parent))
    config_path = root / "config.yaml"
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}


_config = load_config()
# Load .env from root
_root = Path(os.getenv("LAMBDA_TASK_ROOT", Path(__file__).resolve().parent.parent.parent.parent))
load_dotenv(_root / ".env")

CANONICAL_GEMINI_MODEL = "gemini-2.5-flash"


class Settings:
    def __init__(self) -> None:
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or str(_config.get("gemini_api_key") or "")
        self.gemini_model = os.getenv("GEMINI_MODEL") or str(_config.get("gemini_model") or CANONICAL_GEMINI_MODEL)
        self.supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        # Backend database access is trusted/server-side only. Never fall back to a
        # browser-safe anon/publishable key: missing service-role configuration
        # must fail closed instead of silently widening the backend trust model.
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


settings = Settings()
