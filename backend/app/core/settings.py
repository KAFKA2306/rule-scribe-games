import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def load_config() -> dict[str, Any]:
    # Try multiple possible locations for config.yaml
    base_dir = Path(__file__).resolve().parent.parent.parent
    possible_paths = [
        base_dir / "config.yaml",  # backend/config.yaml
        base_dir.parent / "config.yaml",  # host project root/config.yaml
    ]
    for config_path in possible_paths:
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
    return {}


_config = load_config()
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
CANONICAL_GEMINI_MODEL = "gemini-2.5-flash"


class Settings:
    def __init__(self) -> None:
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL") or str(_config.get("gemini_model") or CANONICAL_GEMINI_MODEL)
        self.supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            print("WARNING: Supabase environment variables are missing!")


settings = Settings()
