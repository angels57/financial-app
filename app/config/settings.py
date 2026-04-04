"""Configuración de la aplicación."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Financial Stre"
    debug: bool = False
    db_url: str = ""
    alpha_vantage_api_key: str = ""
    price_cache_ttl_seconds: int = 300
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
    # pydantic-settings BaseSettings has known mypy incompatibility with env var inference
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
