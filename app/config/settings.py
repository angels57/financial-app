"""Configuración de la aplicación."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "app"
    debug: bool = False
    db_url: str = ""
    log_level: str = "INFO"
    log_file: str = "logs/app.json"
    sentry_dsn: str = ""
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación."""
    return Settings()


settings = get_settings()
