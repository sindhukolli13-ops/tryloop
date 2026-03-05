"""
Application configuration loaded from environment variables.
Uses pydantic-settings to validate and type all config values.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All app config — loaded from .env or environment variables."""

    # ── Database ──
    DATABASE_URL: str = "postgresql://tryloop:changeme@postgres:5432/tryloop"

    # ── Redis ──
    REDIS_URL: str = "redis://redis:6379"

    # ── Auth / JWT ──
    JWT_SECRET: str = "change-me-in-production"
    JWT_REFRESH_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Stripe ──
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ── Email (SMTP) ──
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@tryloop.nl"

    # ── OAuth — Google ──
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ── App ──
    APP_ENV: str = "development"
    NEXTAUTH_URL: str = "http://localhost:3000"  # frontend URL for email links

    # ── Sustainability — kg CO₂ saved per device category ──
    CO2_PER_PHONE_KG: float = 70
    CO2_PER_LAPTOP_KG: float = 300
    CO2_PER_TABLET_KG: float = 130
    CO2_PER_WEARABLE_KG: float = 30
    CO2_PER_HEADPHONES_KG: float = 25

    # ── Trial duration options (days) ──
    TRIAL_DURATIONS: list[int] = [7, 14]

    model_config = {"env_file": ".env", "extra": "ignore"}


# Singleton instance — import this wherever config is needed
settings = Settings()
