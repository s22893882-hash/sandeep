"""
Tests for profile management endpoints.
"""
import pytest
from httpx import AsyncClient
from bson import ObjectId


@pytest.mark.asyncio
class TestProfileEndpoints:
    """Test profile management endpoints."""

    async def test_get_profile_success(self, client: AsyncClient, auth_headers: dict, test_user: dict):
        """Test successful profile retrieval."""
        response = await client.get(
            "/api/users/profile",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user["user_id"]
        assert data["email"] == test_user["email"]
        assert data["full_name"] == test_user["full_name"]

    async def test_get_profile_no_auth(self, client: AsyncClient):
        """Test profile retrieval without authentication."""
        response = await client.get("/api/users/profile")
        assert response.status_code == 401

    async def test_get_profile_invalid_token(self, client: AsyncClient):
        """Test profile retrieval with invalid token."""
        response = await client.get(
            "/api/users/profile",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    async def test_update_profile_full_name(self, client: AsyncClient, auth_headers: dict):
        """Test updating profile full name."""
        response = await client.put(
            "/api/users/profile",
            json={"full_name": "Updated Name"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    async def test_update_profile_phone_number(self, client: AsyncClient, auth_headers: dict):
        """Test updating profile phone number."""
        response = await client.put(
            "/api/users/profile",
            json={"phone_number": "+1987654321"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == "+1987654321"

    async def test_update_profile_address(self, client: AsyncClient, auth_headers: dict):
        """Test updating profile address."""
        response = await client.put(
            "/api/users/profile",
            json={"address": "123 New Street, City, Country"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "123 New Street, City, Country"

    async def test_update_profile_multiple_fields(self, client: AsyncClient, auth_headers: dict):
        """Test updating multiple profile fields."""
        response = await client.put(
            "/api/users/profile",
            json={
                "full_name": "Multiple Update",
                "phone_number": "+1555123456",
                "address": "456 Updated Ave",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Multiple Update"
        assert data["phone_number"] == "+1555123456"
        assert data["address"] == "456 Updated Ave"

    async def test_update_profile_partial(self, client: AsyncClient, auth_headers: dict):
        """Test updating profile with empty request (partial update)."""
        response = await client.put(
            "/api/users/profile",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_update_profile_no_auth(self, client: AsyncClient):
        """Test profile update without authentication."""
        response = await client.put(
            "/api/users/profile",
            json={"full_name": "Unauthorized"},
        )
        assert response.status_code == 401

    async def test_update_profile_photo_success(self, client: AsyncClient, auth_headers: dict, test_user: dict):
        """Test successful profile photo upload."""
        # Create a mock image file
        from io import BytesIO

        image_content = b"fake_image_content_for_testing"
        files = {"file": ("profile.jpg", BytesIO(image_content), "image/jpeg")}

        response = await client.put(
            "/api/users/profile/photo",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "photo_url" in data
        assert data["upload_status"] == "success"

    async def test_update_profile_photo_invalid_type(self, client: AsyncClient, auth_headers: dict):
        """Test profile photo upload with invalid file type."""
        from io import BytesIO

        pdf_content = b"%PDF-1.4 fake pdf"
        files = {"file": ("document.pdf", BytesIO(pdf_content), "application/pdf")}

        response = await client.put(
            "/api/users/profile/photo",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    async def test_update_profile_photo_no_auth(self, client: AsyncClient):
        """Test profile photo upload without authentication."""
        from io import BytesIO

        image_content = b"fake_image_content"
        files = {"file": ("profile.jpg", BytesIO(image_content), "image/jpeg")}

        response = await client.put("/api/users/profile/photo", files=files)
        assert response.status_code == 401

    async def test_delete_account_success(self, client: AsyncClient, auth_headers: dict, test_user: dict):
        """Test successful account deletion."""
        response = await client.delete(
            "/api/users/account",
            json={"password": "TestPassword123!"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deletion_status"] == "success"

        # Verify user is soft deleted
        db = test_user.get("db")
        if db:
            user = await db.users.find_one({"_id": ObjectId(test_user["user_id"])})
            assert user["deleted_at"] is not None
            assert user["is_active"] is False

    async def test_delete_account_wrong_password(self, client: AsyncClient, auth_headers: dict):
        """Test account deletion with wrong password."""
        response = await client.delete(
            "/api/users/account",
            json={"password": "WrongPassword123!"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Invalid password" in response.json()["detail"]

    async def test_delete_account_no_auth(self, client: AsyncClient):
        """Test account deletion without authentication."""
        response = await client.delete(
            "/api/users/account",
            json={"password": "TestPassword123!"},
        )
        assert response.status_code == 401
