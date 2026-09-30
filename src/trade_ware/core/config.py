"""Application settings and configuration file."""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )

    app_name: str = ""
    app_base_url: str = ""
    database_user: str = ""
    database_password: str = ""
    database_host: str = ""
    database_port: int = 5432
    database_name: str = ""
    database_url: str | None = None
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    jwt_secret_key: str = "development-only-change-me-32-bytes"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    email_verification_token_expire_minutes: int = 15

    @property
    def resolved_database_url(self) -> str:
        """Construct the database URL from environment values."""
        env_database_url = (
            os.getenv("DATABASE_URL") or self.database_url or ""
        ).strip()
        if env_database_url:
            return env_database_url

        user = self.database_user.strip()
        password = self.database_password.strip()
        host = self.database_host.strip()
        if not user and not password and not host and not self.database_name:
            return "sqlite:///./trade_ware.db"

        return (
            f"postgresql+psycopg://{user}:{password}@{host}:"
            f"{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get the application settings."""
    return Settings()  # type: ignore


settings = get_settings()
