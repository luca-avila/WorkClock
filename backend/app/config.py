"""
Application configuration using pydantic-settings.
Loads settings from environment variables and .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database (async driver)
    DATABASE_URL: str  # Must use postgresql+asyncpg://...

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8

    # CORS
    BACKEND_CORS_ORIGINS: str = '["http://localhost:5173"]'

    # Environment
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except json.JSONDecodeError:
            return ["http://localhost:5173"]


# Global settings instance
settings = Settings()
