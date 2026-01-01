"""E2E test configuration and fixtures."""
import pytest
from typing import Generator
from playwright.sync_api import Page, BrowserContext, Browser


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """Configure browser context."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture
def api_base_url() -> str:
    """Get API base URL for E2E tests."""
    import os
    return os.getenv("E2E_API_URL", "http://localhost:8000")


@pytest.fixture
def page(page: Page, api_base_url: str) -> Page:
    """Configure page with API base URL."""
    page.set_extra_http_headers({"Accept": "application/json"})
    return page


@pytest.fixture
def auth_token(api_base_url: str) -> str:
    """Get auth token for authenticated requests."""
    import requests

    response = requests.post(
        f"{api_base_url}/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    response.raise_for_status()
    return response.json()["access_token"]
