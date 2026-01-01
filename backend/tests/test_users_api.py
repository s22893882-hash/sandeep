"""Tests for Users API endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestUsersAPI:
    """Test suite for Users API."""

    def test_list_users(self):
        """Test listing all users."""
        response = client.get("/users")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # Should have at least the test user

    def test_get_user(self):
        """Test getting a specific user."""
        response = client.get("/users/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "email" in data
        assert "username" in data

    def test_get_user_not_found(self):
        """Test getting a non-existent user."""
        response = client.get("/users/9999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_create_user(self):
        """Test creating a new user."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepassword123",
        }

        response = client.post("/users", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert data["is_active"] is True

    def test_create_user_duplicate_email(self):
        """Test creating a user with duplicate email."""
        user_data = {
            "email": "test@example.com",  # This email already exists
            "username": "anotheruser",
            "password": "password123",
        }

        response = client.post("/users", json=user_data)

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()

    def test_create_user_invalid_email(self):
        """Test creating a user with invalid email."""
        user_data = {
            "email": "notanemail",
            "username": "testuser",
            "password": "password123",
        }

        response = client.post("/users", json=user_data)

        # FastAPI/pydantic validation should catch this
        assert response.status_code == 422

    def test_create_user_short_password(self):
        """Test creating a user with password too short."""
        user_data = {
            "email": "shortpass@example.com",
            "username": "testuser",
            "password": "123",
        }

        response = client.post("/users", json=user_data)

        assert response.status_code == 422

    def test_update_user(self):
        """Test updating an existing user."""
        update_data = {
            "username": "updatedusername",
        }

        response = client.put("/users/1", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updatedusername"

    def test_update_user_email(self):
        """Test updating user email."""
        # First create a user
        create_data = {
            "email": "updatetest@example.com",
            "username": "updatetest",
            "password": "password123",
        }
        create_response = client.post("/users", json=create_data)
        user_id = create_response.json()["id"]

        # Update email
        update_data = {"email": "newemail@example.com"}
        response = client.put(f"/users/{user_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"

    def test_update_user_not_found(self):
        """Test updating a non-existent user."""
        update_data = {"username": "newname"}

        response = client.put("/users/9999", json=update_data)

        assert response.status_code == 404

    def test_delete_user(self):
        """Test deleting a user."""
        # First create a user
        create_data = {
            "email": "deleteuser@example.com",
            "username": "deleteuser",
            "password": "password123",
        }
        create_response = client.post("/users", json=create_data)
        user_id = create_response.json()["id"]

        # Delete the user
        response = client.delete(f"/users/{user_id}")

        assert response.status_code == 204

        # Verify user is deleted
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self):
        """Test deleting a non-existent user."""
        response = client.delete("/users/9999")

        assert response.status_code == 404

    def test_user_response_structure(self):
        """Test that user response has correct structure."""
        response = client.get("/users/1")

        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Verify password is not in response
        assert "password" not in data
        assert "hashed_password" not in data
