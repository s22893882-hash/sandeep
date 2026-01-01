"""
Application configuration settings.
"""

from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Doctor Management API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "doctor_management"

    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Email settings (for verification notifications)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@doctorapp.com"

    # Admin settings
    ADMIN_EMAILS: List[str] = ["admin@doctorapp.com"]

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if v == "your-secret-key-change-in-production" and not cls.DEBUG:
            raise ValueError("SECRET_KEY must be changed in production")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
