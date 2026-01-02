"""
Authentication service for user registration, login, and token management.
"""
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.user import UserCreate, UserLogin
from app.services.email_service import get_email_service
from app.utils.jwt import create_access_token, create_refresh_token, verify_token
from app.utils.otp import generate_otp, get_otp_expiry, is_otp_expired
from app.utils.password import hash_password, verify_password


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncIOMotorDatabase = None):
        """Initialize auth service."""
        self.db: AsyncIOMotorDatabase = db or get_database()
        self.email_service = get_email_service()

    async def register_user(self, user_data: UserCreate) -> dict:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self.db.users.find_one({"email": user_data.email})
        if existing_user:
            raise ValueError("User with this email already exists")

        # Create user document
        user_dict = {
            "email": user_data.email,
            "password_hash": hash_password(user_data.password),
            "full_name": user_data.full_name,
            "phone_number": user_data.phone_number,
            "date_of_birth": user_data.date_of_birth,
            "address": None,
            "profile_photo_url": None,
            "user_type": "patient",  # Default user type
            "verification_status": "pending",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": None,
            "deleted_at": None,
        }

        result = await self.db.users.insert_one(user_dict)
        user_id = str(result.inserted_id)

        # Generate and store OTP
        otp_code = generate_otp()
        await self.db.otps.insert_one(
            {
                "email": user_data.email,
                "otp_code": otp_code,
                "expires_at": get_otp_expiry(),
                "created_at": datetime.utcnow(),
                "used": False,
            }
        )

        # Send OTP email
        await self.email_service.send_otp_email(user_data.email, otp_code)

        return {
            "user_id": user_id,
            "email": user_data.email,
            "verification_status": "pending",
        }

    async def verify_otp(self, email: str, otp_code: str) -> dict:
        """Verify OTP code for email verification."""
        # Find valid OTP
        otp_record = await self.db.otps.find_one({"email": email, "otp_code": otp_code, "used": False})

        if not otp_record:
            return {"verification_status": "failed", "message": "Invalid OTP code"}

        if is_otp_expired(otp_record["expires_at"]):
            return {"verification_status": "failed", "message": "OTP code has expired"}

        # Mark OTP as used
        await self.db.otps.update_one({"_id": otp_record["_id"]}, {"$set": {"used": True}})

        # Update user verification status
        await self.db.users.update_one({"email": email}, {"$set": {"verification_status": "verified"}})

        return {"verification_status": "verified", "message": "Email verified successfully"}

    async def login_user(self, login_data: UserLogin) -> dict:
        """Authenticate user and return tokens."""
        # Find user
        user = await self.db.users.find_one({"email": login_data.email})
        if not user:
            raise ValueError("Invalid email or password")

        if user.get("deleted_at"):
            raise ValueError("Account has been deleted")

        if not user.get("is_active", True):
            raise ValueError("Account is inactive")

        if user.get("verification_status") != "verified":
            raise ValueError("Please verify your email before logging in")

        # Verify password
        if not verify_password(login_data.password, user["password_hash"]):
            raise ValueError("Invalid email or password")

        # Create tokens
        user_id = str(user["_id"])
        token_data = {"sub": user_id, "email": user["email"], "user_type": user["user_type"]}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user_id,
            "user_type": user["user_type"],
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise ValueError("Invalid or expired refresh token")

        # Create new access token
        token_data = {
            "sub": payload["sub"],
            "email": payload["email"],
            "user_type": payload["user_type"],
        }
        access_token = create_access_token(token_data)

        return {"access_token": access_token}

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        try:
            user = await self.db.users.find_one({"_id": ObjectId(user_id), "deleted_at": None})
            if user:
                user["user_id"] = str(user.pop("_id"))
            return user
        except Exception:
            return None

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email."""
        user = await self.db.users.find_one({"email": email, "deleted_at": None})
        if user:
            user["user_id"] = str(user.pop("_id"))
        return user


def get_auth_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuthService:
    """Get auth service instance."""
    return AuthService(db)
