"""
Unit tests for user service.
"""
import pytest
from bson import ObjectId

from app.services.user_service import UserService
from app.models.user import UserUpdate


@pytest.mark.asyncio
@pytest.mark.unit
class TestUserService:
    """Test user service methods."""

    async def test_get_user_profile_success(self, db, test_user):
        """Test successful profile retrieval."""
        service = UserService(db)

        profile = await service.get_user_profile(test_user["user_id"])

        assert profile["user_id"] == test_user["user_id"]
        assert profile["email"] == test_user["email"]
        assert profile["full_name"] == test_user["full_name"]

    async def test_get_user_profile_invalid_id(self, db):
        """Test get_user_profile with invalid ID."""
        service = UserService(db)

        with pytest.raises(ValueError, match="Invalid user ID"):
            await service.get_user_profile("invalid_id")

    async def test_update_user_profile_full_name(self, db, test_user):
        """Test updating user full name."""
        service = UserService(db)

        profile = await service.update_user_profile(test_user["user_id"], UserUpdate(full_name="Updated Name"))

        assert profile["full_name"] == "Updated Name"
        assert profile["user_id"] == test_user["user_id"]

    async def test_update_user_profile_phone_number(self, db, test_user):
        """Test updating user phone number."""
        service = UserService(db)

        profile = await service.update_user_profile(test_user["user_id"], UserUpdate(phone_number="+1987654321"))

        assert profile["phone_number"] == "+1987654321"

    async def test_update_user_profile_address(self, db, test_user):
        """Test updating user address."""
        service = UserService(db)

        profile = await service.update_user_profile(
            test_user["user_id"],
            UserUpdate(address="123 New Street, City, Country"),
        )

        assert profile["address"] == "123 New Street, City, Country"

    async def test_update_user_profile_multiple_fields(self, db, test_user):
        """Test updating multiple profile fields."""
        service = UserService(db)

        profile = await service.update_user_profile(
            test_user["user_id"],
            UserUpdate(
                full_name="Multiple Update",
                phone_number="+1555123456",
                address="456 Updated Ave",
            ),
        )

        assert profile["full_name"] == "Multiple Update"
        assert profile["phone_number"] == "+1555123456"
        assert profile["address"] == "456 Updated Ave"

    async def test_update_user_profile_invalid_id(self, db):
        """Test update_user_profile with invalid ID."""
        service = UserService(db)

        with pytest.raises(ValueError, match="Invalid user ID"):
            await service.update_user_profile("invalid_id", UserUpdate(full_name="Test"))

    async def test_update_profile_photo(self, db, test_user):
        """Test updating profile photo."""
        service = UserService(db)

        result = await service.update_profile_photo(test_user["user_id"], "/api/static/photo.jpg")

        assert result["photo_url"] == "/api/static/photo.jpg"
        assert result["upload_status"] == "success"

    async def test_update_profile_photo_invalid_id(self, db):
        """Test update_profile_photo with invalid ID."""
        service = UserService(db)

        with pytest.raises(ValueError, match="Invalid user ID"):
            await service.update_profile_photo("invalid_id", "/api/static/photo.jpg")

    async def test_soft_delete_user_success(self, db, test_user):
        """Test successful soft delete of user."""
        service = UserService(db)

        result = await service.soft_delete_user(test_user["user_id"], "TestPassword123!")

        assert result["deletion_status"] == "success"

        # Verify user is soft deleted in database
        db = test_user.get("db")
        if db:
            user = await db.users.find_one({"_id": ObjectId(test_user["user_id"])})
            assert user["deleted_at"] is not None
            assert user["is_active"] is False

    async def test_soft_delete_user_wrong_password(self, db, test_user):
        """Test soft delete with wrong password."""
        service = UserService(db)

        with pytest.raises(ValueError, match="Invalid password"):
            await service.soft_delete_user(test_user["user_id"], "WrongPassword!")

    async def test_soft_delete_user_invalid_id(self, db):
        """Test soft delete with invalid user ID."""
        service = UserService(db)

        with pytest.raises(ValueError, match="Invalid user ID"):
            await service.soft_delete_user("invalid_id", "TestPassword123!")
