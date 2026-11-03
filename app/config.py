
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):

    # Application configuration
    app_name: str = "Investment_AI"
    app_env: str = "development"
    debug: bool = False

    # OpenAI configuration
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"

    openai_embedding_model: str = (
        "text-embedding-3-small"
    )

    # Database configuration
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    )
    # Redis configuration
    redis_url: SecretStr = SecretStr(
        "redis://localhost:6379/0"
    )

    # LangSmith configuration
    langsmith_tracing: bool = False
    langsmith_api_key: SecretStr | None = None

    langsmith_project: str = (
        "investment-advice-ai"
    )

    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Load configuration only once
@lru_cache
def get_settings() -> Settings:

    return Settings()


# Global application settings
settings = get_settings()
