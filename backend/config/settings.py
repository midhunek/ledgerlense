"""
Application settings — loaded from .env via pydantic-settings.
Single source of truth for all configuration values.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # OpenAI / Groq
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: Optional[str] = None
    MODERATION_MODEL: str = "omni-moderation-latest"

    # Confidence routing
    REVIEW_THRESHOLD: float = Field(default=0.75, ge=0.0, le=1.0)

    # Cost tracking (USD per token — gpt-4o input pricing approx)
    MODEL_COST_PER_TOKEN: float = 0.000005

    # Storage
    DATABASE_URL: str = "sqlite:///./ledgerlens.db"
    UPLOADS_DIR: str = "uploads"
    PROCESSED_DIR: str = "processed"

    # App
    APP_NAME: str = "LedgerLens"
    DEBUG: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
