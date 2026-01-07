"""
Application configuration and settings.
"""
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # Application
    app_name: str = "Federated Health AI Platform"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "federated_health_ai"

    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Password
    password_min_length: int = 8
    bcrypt_rounds: int = 12

    # OTP
    otp_length: int = 6
    otp_expire_minutes: int = 15

    # Rate Limiting
    rate_limit_login_attempts: int = 5
    rate_limit_login_period: int = 15  # minutes

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Email
    email_from_address: str = "noreply@federatedhealth.ai"
    email_mock_mode: bool = True


settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
