"""Tests for application configuration."""
import os
from unittest.mock import patch

import pytest

from app.config import Settings, get_settings


def test_default_settings():
    """Test default settings values."""
    settings = Settings()
    assert settings.app_name == "FastAPI Application"
    assert settings.app_version == "1.0.0"
    assert settings.debug is False
    assert settings.environment == "development"


def test_settings_from_env():
    """Test loading settings from environment variables."""
    with patch.dict(
        os.environ,
        {
            "APP_NAME": "Test App",
            "APP_VERSION": "2.0.0",
            "DEBUG": "true",
            "ENVIRONMENT": "staging",
        },
        clear=False,
    ):
        settings = Settings()
        assert settings.app_name == "Test App"
        assert settings.app_version == "2.0.0"
        assert settings.debug is True
        assert settings.environment == "staging"


def test_is_production():
    """Test production environment detection."""
    settings = Settings(environment="production")
    assert settings.is_production is True
    assert settings.is_staging is False
    assert settings.is_development is False


def test_is_staging():
    """Test staging environment detection."""
    settings = Settings(environment="staging")
    assert settings.is_production is False
    assert settings.is_staging is True
    assert settings.is_development is False


def test_is_development():
    """Test development environment detection."""
    settings = Settings(environment="development")
    assert settings.is_production is False
    assert settings.is_staging is False
    assert settings.is_development is True


def test_get_settings_caching():
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_cors_origins():
    """Test CORS origins configuration."""
    settings = Settings()
    assert isinstance(settings.cors_origins, list)
    assert "http://localhost:3000" in settings.cors_origins


def test_database_config():
    """Test database configuration."""
    settings = Settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.database_pool_size == 10
    assert settings.database_max_overflow == 20


def test_redis_config():
    """Test Redis configuration."""
    settings = Settings()
    assert settings.redis_url.startswith("redis://")
    assert settings.redis_pool_size == 10


def test_security_config():
    """Test security configuration."""
    settings = Settings()
    assert settings.secret_key
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30


def test_logging_config():
    """Test logging configuration."""
    settings = Settings()
    assert settings.log_level == "INFO"
    assert settings.log_format == "json"


def test_docs_config():
    """Test API documentation configuration."""
    settings = Settings()
    assert settings.docs_enabled is True
    assert settings.docs_url == "/docs"
    assert settings.redoc_url == "/redoc"
