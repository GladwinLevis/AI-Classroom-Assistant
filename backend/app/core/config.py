import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import AnyHttpUrl, BeforeValidator, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated


def parse_cors_origins(v: Any) -> List[str]:
    """Helper to parse CORS origins string or list into a list of strings."""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    """
    Application Settings configuration class.
    Loads and validates environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Core Application Settings
    PROJECT_NAME: str = "AI Classroom Assistant"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    ENVIRONMENT: str = "local"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Annotated[
        List[str], BeforeValidator(parse_cors_origins)
    ] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # Security / Authentication Config
    SECRET_KEY: str = Field("09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7", validation_alias="SECRET_KEY")
    JWT_SECRET_KEY: str = Field("09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7", validation_alias="JWT_SECRET_KEY")
    ALGORITHM: str = Field("HS256", validation_alias="ALGORITHM")
    JWT_ALGORITHM: str = Field("HS256", validation_alias="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database Configuration
    DATABASE_URL: str = Field(
        "postgresql+psycopg://postgres:<POSTGRES_PASSWORD>@localhost:5432/ai_classroom",
        validation_alias="DATABASE_URL"
    )
    SYNC_DATABASE_URL: Optional[str] = Field(None, validation_alias="SYNC_DATABASE_URL")

    @property
    def sync_url(self) -> str:
        """Returns synchronous database URL for Alembic migrations and synchronous drivers."""
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        url = self.DATABASE_URL
        if "postgresql+psycopg://" in url:
            return url.replace("postgresql+psycopg://", "postgresql+psycopg2://")
        elif "postgresql+asyncpg://" in url:
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        elif "sqlite+aiosqlite://" in url:
            return url.replace("sqlite+aiosqlite://", "sqlite://")
        return url

    # Redis and Caching
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery Background Workers
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # File Storage
    STORAGE_PROVIDER: str = "local"
    UPLOAD_DIR: str = "./uploads"

    # AI & RAG Configuration
    GOOGLE_API_KEY: str = Field("test_live_key_12345", validation_alias="GOOGLE_API_KEY")
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "./vector_indices"

    # Audio Configuration
    WHISPER_MODEL_NAME: str = "base"

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"


# Global settings instance
settings = Settings()
