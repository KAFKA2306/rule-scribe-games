from pydantic_settings import BaseSettings
from pydantic import Field
import yaml


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


config = load_config()


class Settings(BaseSettings):
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = config.get("gemini", {}).get("model", "gemini-2.5-flash")

    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
