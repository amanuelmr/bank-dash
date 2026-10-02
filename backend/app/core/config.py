"""Application configuration, loaded from environment variables / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "BankDash API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # --- database -----------------------------------------------------------
    # Swap to `postgresql+asyncpg://...` for Postgres; no other change needed.
    database_url: str = "sqlite+aiosqlite:///./bankdash.db"
    db_echo: bool = False

    # --- auth ---------------------------------------------------------------
    # Override SECRET_KEY in .env for anything beyond local development.
    secret_key: str = "dev-only-insecure-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    refresh_token_expire_days: int = 30

    # --- cors ---------------------------------------------------------------
    cors_origins: list[str] = ["http://localhost:3000"]

    # --- pagination defaults ------------------------------------------------
    default_page_size: int = 10
    max_page_size: int = 100

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()