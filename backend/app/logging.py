"""Application logging configuration."""
import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger

from app.config import get_settings

settings = get_settings()


class CustomFormatter(logging.Formatter):
    """Custom log formatter with color support for development."""

    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: grey + "%(levelname)s" + reset + ": %(message)s",
        logging.INFO: blue + "%(levelname)s" + reset + ": %(message)s",
        logging.WARNING: yellow + "%(levelname)s" + reset + ": %(message)s",
        logging.ERROR: red + "%(levelname)s" + reset + ": %(message)s",
        logging.CRITICAL: bold_red + "%(levelname)s" + reset + ": %(message)s",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record."""
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(
            log_fmt,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        return formatter.format(record)


def setup_logging() -> None:
    """Set up application logging based on environment."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    if settings.is_production or settings.is_staging:
        # JSON logging for production/staging
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            timestamp=True,
        )
    else:
        # Colored logging for development
        formatter = CustomFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding structured logging context."""

    def __init__(self, logger: logging.Logger, **context: Any):
        """Initialize log context."""
        self.logger = logger
        self.context = context

    def __enter__(self):
        """Enter context."""
        extra = {"extra": self.context}
        return logging.LoggerAdapter(self.logger, self.context)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if exc_type is not None:
            self.logger.error(
                "Error in context",
                exc_info=exc_val,
                extra=self.context,
            )
        return False
