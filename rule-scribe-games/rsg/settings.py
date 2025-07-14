# rsg/settings.py
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # ---------- Google Gemini ----------
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = "models/gemini-1.5-pro-latest"
    gemini_embed_model: str = "models/embedding-001"

    # ---------- Vector DB (Qdrant) ------
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    vector_dim: int = 768          # embedding-001 は 768 dims
    collection_name: str = "games"

    # ---------- SQLite ------------------
    database_url: str = "sqlite:///./rsg.db"

    # ---------- Celery ------------------
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    class Config:
        env_file = ".env"


settings = Settings()
