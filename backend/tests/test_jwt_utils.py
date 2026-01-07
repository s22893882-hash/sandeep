"""
Unit tests for JWT utility functions.
"""
import pytest
from datetime import timedelta

from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
)


@pytest.mark.unit
class TestJWTUtils:
    """Test JWT utility functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)

    def test_create_access_token_with_expiry(self):
        """Test access token creation with custom expiry."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data, expires_delta=timedelta(minutes=30))

        assert token is not None

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        payload = decode_token("invalid_token")

        assert payload is None

    def test_verify_access_token(self):
        """Test verifying an access token."""
        data = {"sub": "user123", "email": "test@example.com", "user_type": "patient"}
        token = create_access_token(data)

        payload = verify_token(token, "access")

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_verify_refresh_token(self):
        """Test verifying a refresh token."""
        data = {"sub": "user123", "email": "test@example.com", "user_type": "patient"}
        token = create_refresh_token(data)

        payload = verify_token(token, "refresh")

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self):
        """Test verifying token with wrong type."""
        data = {"sub": "user123", "email": "test@example.com"}
        access_token = create_access_token(data)

        payload = verify_token(access_token, "refresh")

        assert payload is None
