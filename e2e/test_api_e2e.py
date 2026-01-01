"""E2E tests for API endpoints using Playwright."""
import pytest
import requests
import json
from typing import Generator


class TestHealthEndpoints:
    """E2E tests for health endpoints."""

    @pytest.fixture
    def api_base_url(self) -> str:
        """Get API base URL."""
        import os
        return os.getenv("E2E_API_URL", "http://localhost:8000")

    def test_health_check(self, api_base_url: str):
        """Test health check endpoint."""
        response = requests.get(f"{api_base_url}/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

    def test_root_endpoint(self, api_base_url: str):
        """Test root endpoint."""
        response = requests.get(f"{api_base_url}/")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "version" in data

    def test_config_endpoint(self, api_base_url: str):
        """Test configuration endpoint."""
        response = requests.get(f"{api_base_url}/config")

        assert response.status_code == 200
        data = response.json()

        assert "app_name" in data
        assert "version" in data
        assert "environment" in data


class TestAuthFlow:
    """E2E tests for authentication flow."""

    @pytest.fixture
    def api_base_url(self) -> str:
        """Get API base URL."""
        import os
        return os.getenv("E2E_API_URL", "http://localhost:8000")

    def test_complete_auth_flow(self, api_base_url: str):
        """Test complete authentication flow: login, verify, refresh."""
        # Step 1: Login
        login_response = requests.post(
            f"{api_base_url}/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        token = login_data["access_token"]

        # Step 2: Verify token
        verify_response = requests.post(
            f"{api_base_url}/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert verify_response.status_code == 200
        user_data = verify_response.json()
        assert user_data["email"] == "test@example.com"

        # Step 3: Refresh token
        refresh_response = requests.post(
            f"{api_base_url}/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        new_token = refresh_data["access_token"]

        # New token should be different
        assert new_token != token

        # Step 4: Verify new token
        verify_new_response = requests.post(
            f"{api_base_url}/auth/verify",
            headers={"Authorization": f"Bearer {new_token}"},
        )

        assert verify_new_response.status_code == 200


class TestItemsFlow:
    """E2E tests for items CRUD flow."""

    @pytest.fixture
    def api_base_url(self) -> str:
        """Get API base URL."""
        import os
        return os.getenv("E2E_API_URL", "http://localhost:8000")

    @pytest.fixture
    def auth_token(self, api_base_url: str) -> str:
        """Get auth token for requests."""
        response = requests.post(
            f"{api_base_url}/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        return response.json()["access_token"]

    def test_items_crud_flow(self, api_base_url: str, auth_token: str):
        """Test complete items CRUD flow."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: List items
        list_response = requests.get(f"{api_base_url}/items", headers=headers)
        assert list_response.status_code == 200
        items = list_response.json()
        initial_count = len(items)

        # Step 2: Create item
        new_item = {
            "name": "E2E Test Item",
            "description": "Created during E2E test",
            "price": 49.99,
            "quantity": 25,
        }

        create_response = requests.post(
            f"{api_base_url}/items", json=new_item, headers=headers
        )
        assert create_response.status_code == 201
        created_item = create_response.json()
        item_id = created_item["id"]

        # Verify created item
        assert created_item["name"] == new_item["name"]
        assert created_item["price"] == new_item["price"]

        # Step 3: Get specific item
        get_response = requests.get(f"{api_base_url}/items/{item_id}", headers=headers)
        assert get_response.status_code == 200
        retrieved_item = get_response.json()
        assert retrieved_item["id"] == item_id

        # Step 4: Update item
        update_data = {
            "name": "Updated E2E Item",
            "price": 59.99,
        }

        update_response = requests.put(
            f"{api_base_url}/items/{item_id}", json=update_data, headers=headers
        )
        assert update_response.status_code == 200
        updated_item = update_response.json()
        assert updated_item["name"] == update_data["name"]
        assert updated_item["price"] == update_data["price"]

        # Step 5: Delete item
        delete_response = requests.delete(
            f"{api_base_url}/items/{item_id}", headers=headers
        )
        assert delete_response.status_code == 204

        # Step 6: Verify deletion
        verify_delete_response = requests.get(
            f"{api_base_url}/items/{item_id}", headers=headers
        )
        assert verify_delete_response.status_code == 404

        # Step 7: Verify count returned to initial
        final_list_response = requests.get(f"{api_base_url}/items", headers=headers)
        final_items = final_list_response.json()
        assert len(final_items) == initial_count


class TestUsersFlow:
    """E2E tests for users CRUD flow."""

    @pytest.fixture
    def api_base_url(self) -> str:
        """Get API base URL."""
        import os
        return os.getenv("E2E_API_URL", "http://localhost:8000")

    @pytest.fixture
    def auth_token(self, api_base_url: str) -> str:
        """Get auth token for requests."""
        response = requests.post(
            f"{api_base_url}/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        return response.json()["access_token"]

    def test_users_crud_flow(self, api_base_url: str, auth_token: str):
        """Test complete users CRUD flow."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: List users
        list_response = requests.get(f"{api_base_url}/users", headers=headers)
        assert list_response.status_code == 200
        users = list_response.json()
        initial_count = len(users)

        # Step 2: Create user
        new_user = {
            "email": "e2euser@example.com",
            "username": "e2euser",
            "password": "securepassword123",
        }

        create_response = requests.post(
            f"{api_base_url}/users", json=new_user, headers=headers
        )
        assert create_response.status_code == 201
        created_user = create_response.json()
        user_id = created_user["id"]

        # Verify created user
        assert created_user["email"] == new_user["email"]
        assert created_user["username"] == new_user["username"]
        assert "password" not in created_user  # Password should not be in response

        # Step 3: Get specific user
        get_response = requests.get(f"{api_base_url}/users/{user_id}", headers=headers)
        assert get_response.status_code == 200
        retrieved_user = get_response.json()
        assert retrieved_user["id"] == user_id

        # Step 4: Update user
        update_data = {
            "username": "updatede2euser",
        }

        update_response = requests.put(
            f"{api_base_url}/users/{user_id}", json=update_data, headers=headers
        )
        assert update_response.status_code == 200
        updated_user = update_response.json()
        assert updated_user["username"] == update_data["username"]

        # Step 5: Delete user
        delete_response = requests.delete(
            f"{api_base_url}/users/{user_id}", headers=headers
        )
        assert delete_response.status_code == 204

        # Step 6: Verify deletion
        verify_delete_response = requests.get(
            f"{api_base_url}/users/{user_id}", headers=headers
        )
        assert verify_delete_response.status_code == 404


class TestErrorHandling:
    """E2E tests for error handling."""

    @pytest.fixture
    def api_base_url(self) -> str:
        """Get API base URL."""
        import os
        return os.getenv("E2E_API_URL", "http://localhost:8000")

    def test_invalid_endpoint(self, api_base_url: str):
        """Test accessing invalid endpoint."""
        response = requests.get(f"{api_base_url}/invalid-endpoint")

        assert response.status_code == 404

    def test_invalid_method(self, api_base_url: str):
        """Test using invalid HTTP method."""
        response = requests.post(f"{api_base_url}/items")

        # Should fail without required fields
        assert response.status_code == 422

    def test_nonexistent_item(self, api_base_url: str):
        """Test accessing non-existent item."""
        response = requests.get(f"{api_base_url}/items/999999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_nonexistent_user(self, api_base_url: str):
        """Test accessing non-existent user."""
        response = requests.get(f"{api_base_url}/users/999999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
