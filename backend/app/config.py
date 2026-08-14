"""
Pulse — Application Configuration
Loads from .env with sensible defaults for demo mode.
"""

# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ──
    app_name: str = "Pulse"
    app_env: str = "development"
    demo_mode: bool = True
    log_level: str = "info"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # ── Database ──
    database_url: str = "postgresql+asyncpg://pulse:pulse_dev_2026@localhost:5432/pulse"
    redis_url: str = "redis://localhost:6379/0"

    # ── LLM Keys ──
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # ── LangSmith ──
    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = "pulse"

    # ── Platform APIs ──
    meta_app_id: Optional[str] = None
    meta_app_secret: Optional[str] = None
    meta_access_token: Optional[str] = None

    # ── Generation Settings ──
    max_variants: int = 3
    voice_similarity_threshold: float = 0.75
    slop_check_enabled: bool = True
    max_retries: int = 2

    # ── Rate Limits ──
    auto_reply_rate_limit: int = 200  # per hour per account (Meta cap)
    sentiment_spike_threshold: float = -0.6
    sentiment_spike_window_minutes: int = 30

    # ── Embedding ──
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
