"""Application configuration with environment support."""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "FastAPI Application"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")

    # Environment
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/app_db",
        description="Database connection URL",
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_pool_size: int = 10

    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="CORS allowed origins",
    )

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # External Services
    stripe_api_key: Optional[str] = Field(
        default=None,
        description="Stripe API key for payments",
    )
    aws_region: str = "us-east-1"
    s3_bucket: Optional[str] = Field(
        default=None,
        description="S3 bucket name for file storage",
    )

    # API Documentation
    docs_enabled: bool = Field(default=True, description="Enable API documentation")
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == "staging"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
