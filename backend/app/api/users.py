"""Users API routes."""
from typing import List
import uuid

from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext

from app.logging import get_logger
from app.models import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory storage (replace with database in production)
users_db: dict[str, dict] = {
    "test@example.com": {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "hashed_password": pwd_context.hash("password123"),
        "is_active": True,
    },
}
user_id_counter = 2


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


@router.get("", response_model=List[UserResponse])
async def list_users() -> List[UserResponse]:
    """List all users."""
    logger.info("Listing users")

    return [
        UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            is_active=user["is_active"],
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at"),
        )
        for user in users_db.values()
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int) -> UserResponse:
    """Get a specific user by ID."""
    logger.info("Getting user", extra={"user_id": user_id})

    for user in users_db.values():
        if user["id"] == user_id:
            return UserResponse(
                id=user["id"],
                email=user["email"],
                username=user["username"],
                is_active=user["is_active"],
                created_at=user.get("created_at"),
                updated_at=user.get("updated_at"),
            )

    logger.warning("User not found", extra={"user_id": user_id})
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"User with ID {user_id} not found",
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate) -> UserResponse:
    """Create a new user."""
    global user_id_counter

    logger.info("Creating user", extra={"email": user.email, "username": user.username})

    # Check if user already exists
    if user.email in users_db:
        logger.warning("User already exists", extra={"email": user.email})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Create new user
    new_user = {
        "id": user_id_counter,
        "email": user.email,
        "username": user.username,
        "hashed_password": get_password_hash(user.password),
        "is_active": True,
    }
    users_db[user.email] = new_user
    user_id_counter += 1

    logger.info("User created successfully", extra={"user_id": new_user["id"]})

    return UserResponse(
        id=new_user["id"],
        email=new_user["email"],
        username=new_user["username"],
        is_active=new_user["is_active"],
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate) -> UserResponse:
    """Update an existing user."""
    logger.info("Updating user", extra={"user_id": user_id})

    # Find user
    user_data = None
    user_email = None
    for email, data in users_db.items():
        if data["id"] == user_id:
            user_data = data
            user_email = email
            break

    if not user_data:
        logger.warning("User not found", extra={"user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    # Update only provided fields
    update_data = user.model_dump(exclude_unset=True)

    # If email is being updated, check if new email already exists
    if "email" in update_data and update_data["email"] != user_email:
        if update_data["email"] in users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )
        # Move user to new email key
        del users_db[user_email]
        user_email = update_data["email"]

    user_data.update(update_data)

    logger.info("User updated successfully", extra={"user_id": user_id})

    return UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        username=user_data["username"],
        is_active=user_data["is_active"],
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int) -> None:
    """Delete a user."""
    logger.info("Deleting user", extra={"user_id": user_id})

    # Find and delete user
    user_email = None
    for email, data in users_db.items():
        if data["id"] == user_id:
            user_email = email
            break

    if not user_email:
        logger.warning("User not found", extra={"user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    del users_db[user_email]
    logger.info("User deleted successfully", extra={"user_id": user_id})
