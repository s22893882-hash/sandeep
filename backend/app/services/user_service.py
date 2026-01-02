"""
User service for profile management.
"""
from datetime import datetime

from bson import ObjectId
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.database import get_database
from app.models.user import UserUpdate
from app.utils.password import verify_password


class UserService:
    """Service for user profile operations."""

    def __init__(self, db: AsyncIOMotorDatabase = None):
        """Initialize user service."""
        self.db: AsyncIOMotorDatabase = db or get_database()

    async def get_user_profile(self, user_id: str) -> dict:
        """Get user profile by ID."""
        try:
            user = await self.db.users.find_one({"_id": ObjectId(user_id), "deleted_at": None})
            if not user:
                raise ValueError("User not found")

            # Return user data
            return {
                "user_id": str(user["_id"]),
                "email": user["email"],
                "full_name": user["full_name"],
                "phone_number": user.get("phone_number"),
                "date_of_birth": user.get("date_of_birth"),
                "address": user.get("address"),
                "profile_photo_url": user.get("profile_photo_url"),
                "user_type": user["user_type"],
                "verification_status": user["verification_status"],
                "created_at": user["created_at"],
                "updated_at": user.get("updated_at"),
            }
        except ValueError:
            raise
        except Exception:
            raise ValueError("Invalid user ID")

    async def update_user_profile(self, user_id: str, update_data: UserUpdate) -> dict:
        """Update user profile."""
        try:
            # Build update document with only provided fields
            update_dict = {"updated_at": datetime.utcnow()}
            if update_data.full_name is not None:
                update_dict["full_name"] = update_data.full_name
            if update_data.phone_number is not None:
                update_dict["phone_number"] = update_data.phone_number
            if update_data.address is not None:
                update_dict["address"] = update_data.address

            user = await self.db.users.find_one_and_update(
                {"_id": ObjectId(user_id), "deleted_at": None},
                {"$set": update_dict},
                return_document=ReturnDocument.AFTER,
            )

            if not user:
                raise ValueError("User not found")

            return {
                "user_id": str(user["_id"]),
                "email": user["email"],
                "full_name": user["full_name"],
                "phone_number": user.get("phone_number"),
                "date_of_birth": user.get("date_of_birth"),
                "address": user.get("address"),
                "profile_photo_url": user.get("profile_photo_url"),
                "user_type": user["user_type"],
                "verification_status": user["verification_status"],
                "created_at": user["created_at"],
                "updated_at": user["updated_at"],
            }
        except ValueError:
            raise
        except Exception:
            raise ValueError("Invalid user ID")

    async def update_profile_photo(self, user_id: str, photo_url: str) -> dict:
        """Update user profile photo."""
        try:
            user = await self.db.users.find_one_and_update(
                {"_id": ObjectId(user_id), "deleted_at": None},
                {
                    "$set": {
                        "profile_photo_url": photo_url,
                        "updated_at": datetime.utcnow(),
                    }
                },
                return_document=ReturnDocument.AFTER,
            )

            if not user:
                raise ValueError("User not found")

            return {
                "photo_url": user.get("profile_photo_url"),
                "upload_status": "success",
            }
        except ValueError:
            raise
        except Exception:
            raise ValueError("Invalid user ID")

    async def soft_delete_user(self, user_id: str, password: str) -> dict:
        """Soft delete user account."""
        try:
            user = await self.db.users.find_one({"_id": ObjectId(user_id), "deleted_at": None})

            if not user:
                raise ValueError("User not found")

            # Verify password before deletion
            if not verify_password(password, user["password_hash"]):
                raise ValueError("Invalid password")

            # Soft delete by setting deleted_at
            await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "deleted_at": datetime.utcnow(),
                        "is_active": False,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            return {
                "deletion_status": "success",
                "message": "Account deleted successfully",
            }
        except ValueError:
            raise
        except Exception:
            raise ValueError("Invalid user ID")


def get_user_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UserService:
    """Get user service instance."""
    return UserService(db)
