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

    # --- auth cookies -------------------------------------------------------
    # Tokens are delivered as httpOnly cookies so page scripts cannot read them,
    # which closes the XSS token-exfiltration hole. The API still accepts an
    # Authorization: Bearer header, so CLI and test clients keep working.
    access_cookie_name: str = "accessToken"
    refresh_cookie_name: str = "refreshToken"

    # Must be True wherever the app is served over HTTPS. Browsers drop
    # Secure cookies sent over plain http, so it stays False for localhost dev.
    cookie_secure: bool = False

    # "lax" works while the frontend and API are same-site (localhost:3000 ->
    # localhost:8000). A separately-hosted production frontend is cross-site and
    # needs "none", which browsers only accept together with Secure.
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None

    # --- cors ---------------------------------------------------------------
    # Credentials must be allowed for cookie auth to work cross-origin.
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