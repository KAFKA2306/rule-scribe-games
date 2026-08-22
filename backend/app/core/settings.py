import os
from pathlib import Path

from dotenv import load_dotenv

_root = Path(os.getenv("LAMBDA_TASK_ROOT", Path(__file__).resolve().parent.parent.parent.parent))
load_dotenv(_root / ".env")


class Settings:
    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


settings = Settings()
