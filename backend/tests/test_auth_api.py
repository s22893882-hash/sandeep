"""Tests for Authentication API endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAuthAPI:
    """Test suite for Authentication API."""

    def test_login_success(self):
        """Test successful login."""
        login_data = {
            "email": "test@example.com",
            "password": "password123",
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert isinstance(data["access_token"], str)

    def test_login_invalid_email(self):
        """Test login with non-existent email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123",
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_invalid_password(self):
        """Test login with invalid password."""
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword",
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()

    def test_login_missing_fields(self):
        """Test login with missing required fields."""
        login_data = {
            "email": "test@example.com",
            # Missing password
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 422

    def test_login_invalid_email_format(self):
        """Test login with invalid email format."""
        login_data = {
            "email": "notanemail",
            "password": "password123",
        }

        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 422

    def test_verify_token_success(self):
        """Test successful token verification."""
        # First login to get a token
        login_data = {
            "email": "test@example.com",
            "password": "password123",
        }
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]

        # Verify token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/auth/verify", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["email"] == "test@example.com"
        assert "username" in data

    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        headers = {"Authorization": "Bearer invalidtoken123"}

        response = client.post("/auth/verify", headers=headers)

        assert response.status_code == 401

    def test_verify_token_missing(self):
        """Test token verification without token."""
        response = client.post("/auth/verify")

        assert response.status_code == 403

    def test_refresh_token_success(self):
        """Test successful token refresh."""
        # First login to get a token
        login_data = {
            "email": "test@example.com",
            "password": "password123",
        }
        login_response = client.post("/auth/login", json=login_data)
        old_token = login_response.json()["access_token"]

        # Refresh token
        headers = {"Authorization": f"Bearer {old_token}"}
        response = client.post("/auth/refresh", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # New token should be different
        assert data["access_token"] != old_token

    def test_refresh_token_invalid(self):
        """Test token refresh with invalid token."""
        headers = {"Authorization": "Bearer invalidtoken123"}

        response = client.post("/auth/refresh", headers=headers)

        assert response.status_code == 401

    def test_token_structure(self):
        """Test that token has expected structure."""
        login_data = {
            "email": "test@example.com",
            "password": "password123",
        }
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        # Verify token response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data

        # Verify types
        assert isinstance(data["access_token"], str)
        assert isinstance(data["token_type"], str)
        assert isinstance(data["expires_in"], int)

        # Verify values
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_protected_endpoint_with_token(self):
        """Test accessing a protected endpoint with valid token."""
        # Login to get token
        login_data = {
            "email": "test@example.com",
            "password": "password123",
        }
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]

        # Access users endpoint (which would require auth in real implementation)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/users", headers=headers)

        # Should succeed (currently no auth required on users endpoint)
        assert response.status_code == 200
