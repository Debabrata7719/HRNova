"""
Centralized configuration for NovaHR.
All settings are loaded from environment variables / .env file.
Missing required values raise a clear error at startup — no silent None surprises.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── LLM ──────────────────────────────────────────────────────────
    GROQ_API_KEY: str

    # ── Email (Gmail SMTP) ────────────────────────────────────────────
    EMAIL_ADDRESS: str = ""
    EMAIL_APP_PASSWORD: str = ""

    # ── MySQL ─────────────────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "novahr"

    # ── JWT ───────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev_secret_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_HOURS: int = 8

    # ── LangSmith (optional) ──────────────────────────────────────────
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_PROJECT: str = "novahr"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore unknown env vars


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance — loaded once at startup."""
    return Settings()
