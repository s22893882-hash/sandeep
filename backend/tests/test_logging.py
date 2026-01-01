"""Tests for logging configuration."""
import logging
import sys
from unittest.mock import patch, MagicMock

import pytest
import json

from app.logging import setup_logging, get_logger, LogContext


def test_setup_logging_dev_mode(monkeypatch):
    """Test logging setup in development mode."""
    from app.config import Settings

    # Mock settings for development
    mock_settings = Settings(
        environment="development",
        log_level="INFO",
        log_format="text",
    )

    with patch("app.logging.get_settings", return_value=mock_settings):
        setup_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0


def test_setup_logging_production_mode(monkeypatch):
    """Test logging setup in production mode."""
    from app.config import Settings

    # Mock settings for production
    mock_settings = Settings(
        environment="production",
        log_level="WARNING",
        log_format="json",
    )

    with patch("app.logging.get_settings", return_value=mock_settings):
        setup_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING
        assert len(root_logger.handlers) > 0


def test_get_logger():
    """Test getting a logger instance."""
    setup_logging()
    logger = get_logger("test_logger")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"


def test_log_context_manager():
    """Test LogContext manager."""
    setup_logging()
    logger = get_logger("test_logger")

    with LogContext(logger, user_id=123, action="test") as log_adapter:
        assert isinstance(log_adapter, logging.LoggerAdapter)

    # Context should handle exceptions
    try:
        with LogContext(logger, user_id=456):
            raise ValueError("Test error")
    except ValueError:
        pass  # Expected


def test_log_context_with_error():
    """Test LogContext with exception."""
    setup_logging()
    logger = get_logger("test_logger")

    with patch.object(logger, "error") as mock_error:
        try:
            with LogContext(logger, test_context="value"):
                raise RuntimeError("Test exception")
        except RuntimeError:
            pass

        # Verify error was logged
        assert mock_error.called


def test_logger_levels():
    """Test different log levels."""
    setup_logging()
    logger = get_logger("test_logger")

    # These should not raise exceptions
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")


def test_logger_with_extra():
    """Test logging with extra context."""
    setup_logging()
    logger = get_logger("test_logger")

    # These should not raise exceptions
    logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})
    logger.error("Failed operation", extra={"operation": "delete", "resource_id": 456})
