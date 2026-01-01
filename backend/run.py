#!/usr/bin/env python3
"""
Entry point for running the FastAPI application.

This script provides a convenient way to start the application
with different configurations.
"""
import sys
import uvicorn
from app.config import get_settings


def main():
    """Main entry point."""
    settings = get_settings()

    print(f"\n🚀 Starting {settings.app_name}")
    print(f"   Version: {settings.app_version}")
    print(f"   Environment: {settings.environment}")
    print(f"   Debug: {settings.debug}")
    print(f"   API Docs: {settings.docs_url}")
    print()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=settings.workers if settings.is_production else 1,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
