"""
Unit tests for authentication service.
"""
import pytest
from datetime import datetime, timedelta
from bson import ObjectId

from app.services.auth_service import AuthService
from app.models.user import UserCreate, UserLogin
from app.utils.otp import get_otp_expiry


@pytest.mark.asyncio
@pytest.mark.unit
class TestAuthService:
    """Test authentication service methods."""

    async def test_register_user_creates_account(self, db):
        """Test that register_user creates a user account."""
        service = AuthService(db)

        user_data = UserCreate(
            email="newuser@example.com",
            password="TestPassword123!",
            full_name="New User",
            phone_number="+1234567890",
            date_of_birth=datetime(1990, 1, 1),
        )

        result = await service.register_user(user_data)

        assert "user_id" in result
        assert result["email"] == "newuser@example.com"
        assert result["verification_status"] == "pending"

        # Verify user in database
        user = await db.users.find_one({"email": "newuser@example.com"})
        assert user is not None
        assert user["full_name"] == "New User"

    async def test_register_user_duplicate_email_fails(self, db, test_user):
        """Test that register_user fails with duplicate email."""
        service = AuthService(db)

        with pytest.raises(ValueError, match="already exists"):
            await service.register_user(
                UserCreate(
                    email=test_user["email"],
                    password="TestPassword123!",
                    full_name="Duplicate User",
                )
            )

    async def test_register_user_generates_otp(self, db):
        """Test that register_user generates and stores OTP."""
        service = AuthService(db)

        user_data = UserCreate(
            email="otpuser@example.com",
            password="TestPassword123!",
            full_name="OTP User",
        )

        await service.register_user(user_data)

        # Check OTP was created
        otp = await db.otps.find_one({"email": "otpuser@example.com"})
        assert otp is not None
        assert "otp_code" in otp
        assert len(otp["otp_code"]) == 6
        assert otp["used"] is False

    async def test_verify_otp_success(self, db, test_user):
        """Test successful OTP verification."""
        service = AuthService(db)

        otp_record = await db.otps.find_one({"email": test_user["email"]})
        otp_code = otp_record["otp_code"]

        result = await service.verify_otp(test_user["email"], otp_code)

        assert result["verification_status"] == "verified"

        # Check OTP is marked as used
        updated_otp = await db.otps.find_one({"_id": otp_record["_id"]})
        assert updated_otp["used"] is True

        # Check user is verified
        user = await db.users.find_one({"_id": ObjectId(test_user["user_id"])})
        assert user["verification_status"] == "verified"

    async def test_verify_otp_invalid_code(self, db, test_user):
        """Test OTP verification with invalid code."""
        service = AuthService(db)

        result = await service.verify_otp(test_user["email"], "000000")

        assert result["verification_status"] == "failed"

    async def test_verify_otp_expired_code(self, db, test_user):
        """Test OTP verification with expired code."""
        service = AuthService(db)

        # Create an expired OTP
        expired_otp = await db.otps.insert_one(
            {
                "email": test_user["email"],
                "otp_code": "999999",
                "expires_at": datetime.utcnow() - timedelta(hours=1),
                "created_at": datetime.utcnow() - timedelta(hours=1),
                "used": False,
            }
        )

        result = await service.verify_otp(test_user["email"], "999999")

        assert result["verification_status"] == "failed"

        # Cleanup
        await db.otps.delete_one({"_id": expired_otp.inserted_id})

    async def test_login_user_success(self, db, verified_user):
        """Test successful user login."""
        service = AuthService(db)

        result = await service.login_user(UserLogin(email=verified_user["email"], password="TestPassword123!"))

        assert "access_token" in result
        assert "refresh_token" in result
        assert "user_id" in result
        assert "user_type" in result

    async def test_login_user_invalid_password(self, db, verified_user):
        """Test login with invalid password."""
        service = AuthService(db)

        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.login_user(UserLogin(email=verified_user["email"], password="WrongPassword!"))

    async def test_login_user_nonexistent(self, db):
        """Test login with non-existent user."""
        service = AuthService(db)

        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.login_user(UserLogin(email="nonexistent@example.com", password="TestPassword123!"))

    async def test_login_user_unverified(self, db, test_user):
        """Test login with unverified user."""
        service = AuthService(db)

        with pytest.raises(ValueError, match="verify your email"):
            await service.login_user(UserLogin(email=test_user["email"], password="TestPassword123!"))

    async def test_refresh_token_valid(self, db, verified_user):
        """Test successful token refresh."""
        service = AuthService(db)

        # First login to get refresh token
        login_result = await service.login_user(UserLogin(email=verified_user["email"], password="TestPassword123!"))

        result = await service.refresh_token(login_result["refresh_token"])

        assert "access_token" in result

    async def test_refresh_token_invalid(self, db):
        """Test refresh token with invalid token."""
        service = AuthService(db)

        with pytest.raises(ValueError, match="Invalid or expired"):
            await service.refresh_token("invalid_token")

    async def test_get_user_by_id_success(self, db, test_user):
        """Test get_user_by_id with valid ID."""
        service = AuthService(db)

        user = await service.get_user_by_id(test_user["user_id"])

        assert user is not None
        assert user["user_id"] == test_user["user_id"]
        assert user["email"] == test_user["email"]

    async def test_get_user_by_id_invalid(self, db):
        """Test get_user_by_id with invalid ID."""
        service = AuthService(db)

        user = await service.get_user_by_id("invalid_id")

        assert user is None

    async def test_get_user_by_email_success(self, db, test_user):
        """Test get_user_by_email with valid email."""
        service = AuthService(db)

        user = await service.get_user_by_email(test_user["email"])

        assert user is not None
        assert user["email"] == test_user["email"]

    async def test_get_user_by_email_nonexistent(self, db):
        """Test get_user_by_email with non-existent email."""
        service = AuthService(db)

        user = await service.get_user_by_email("nonexistent@example.com")

        assert user is None
