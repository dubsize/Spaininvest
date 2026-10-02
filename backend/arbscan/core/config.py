"""Application settings, loaded from environment variables (see .env.example)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- core -------------------------------------------------------------
    environment: str = "development"
    database_url: str = "postgresql+psycopg://arbscan:arbscan@localhost:5432/arbscan"
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    log_json: bool = True

    # --- auth (single user) ------------------------------------------------
    admin_username: str = "admin"
    # Either a bcrypt hash (preferred) or a plaintext password for local dev.
    admin_password_hash: str = ""
    admin_password: str = ""
    jwt_secret: str = "change-me-in-.env"
    session_hours: int = 24 * 7
    cookie_secure: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    api_rate_limit_per_minute: int = 600
    login_rate_limit_per_minute: int = 10

    # --- business defaults --------------------------------------------------
    default_resale_country: str = "ES"
    base_currency: str = "EUR"
    default_target_roi: float = 0.25
    default_min_roi: float = 0.15

    # --- scanning -----------------------------------------------------------
    scanner_enabled: bool = True
    scanner_tick_seconds: int = 60
    http_user_agent: str = "ArbScanBot/0.2 (+personal research; contact: set HTTP_CONTACT)"
    http_contact: str = ""
    http_proxy: str = ""  # only set if you are entitled to use it
    http_timeout_seconds: float = 20.0
    respect_robots_txt: bool = True

    # --- connectors ---------------------------------------------------------
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_environment: str = "production"  # or "sandbox"
    ebay_affiliate_campaign_id: str = ""

    # --- alerts -------------------------------------------------------------
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    alert_email_to: str = ""
    smtp_starttls: bool = True
    public_web_url: str = "http://localhost:3000"

    # --- optional AI normalisation -------------------------------------------
    ai_normalizer: str = "none"  # none | anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"
    ai_min_rule_confidence: float = 0.6

    # --- FX --------------------------------------------------------------
    fx_auto_update: bool = False  # fetch ECB reference rates daily when enabled

    # --- demo ---------------------------------------------------------------
    seed_demo_data: bool = True

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
