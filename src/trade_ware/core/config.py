"""Application settings and configuration file."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )
    app_name: str
    database_user: str
    database_password: str
    database_host: str
    database_port: int
    database_name: str

    @property
    def database_url(self) -> str:
        """Construct the database URL from individual components."""
        return (
            f"postgresql+psycopg://{self.database_user}:"
            f"{self.database_password}@"
            f"{self.database_host}:"
            f"{self.database_port}/"
            f"{self.database_name}"
        )

@lru_cache
def get_settings() -> Settings:
    """Get the application settings."""
    return Settings() # type: ignore

settings = get_settings()
