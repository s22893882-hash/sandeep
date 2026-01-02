"""
Profile management routes.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status

from app.models.user import (
    AccountDeletionRequest,
    AccountDeletionResponse,
    UserUpdate,
    UserResponse,
)
from app.services.auth_service import AuthService, get_auth_service
from app.services.user_service import UserService, get_user_service
from app.utils.jwt import verify_token

router = APIRouter(prefix="/api/users", tags=["Profile"])


async def get_current_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    auth_service: AuthService = Depends(get_auth_service),
) -> str:
    """Extract and verify user ID from authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Verify user exists
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user_id


@router.get("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """Get authenticated user's profile."""
    try:
        profile = await user_service.get_user_profile(user_id)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        ) from e


@router.put("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    profile_data: UserUpdate,
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """Update authenticated user's profile."""
    try:
        profile = await user_service.update_user_profile(user_id, profile_data)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        ) from e


@router.put("/profile/photo", status_code=status.HTTP_200_OK)
async def update_profile_photo(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """Upload and update user's profile photo."""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, and WebP are allowed.",
        )

    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit.",
        )

    # In a real implementation, this would upload to S3 or cloud storage
    # For now, we simulate the upload and return a mock URL
    timestamp = int(datetime.utcnow().timestamp())
    photo_url = f"/api/static/profile-photos/{user_id}-{timestamp}.jpg"

    result = await user_service.update_profile_photo(user_id, photo_url)
    return result


@router.delete(
    "/account",
    response_model=AccountDeletionResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_account(
    deletion_data: AccountDeletionRequest,
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    """Delete authenticated user's account."""
    try:
        result = await user_service.soft_delete_user(user_id, deletion_data.password)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account",
        ) from e
