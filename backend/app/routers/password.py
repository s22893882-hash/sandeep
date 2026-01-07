"""
Password reset routes.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings
from app.models.password_reset import (
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    PasswordResetVerifyRequest,
    PasswordResetVerifyResponse,
)
from app.services.auth_service import AuthService, get_auth_service
from app.services.email_service import get_email_service
from app.utils.otp import generate_otp, get_otp_expiry, is_otp_expired
from app.utils.password import hash_password

settings = get_settings()
router = APIRouter(prefix="/api/users", tags=["Password"])
limiter = Limiter(key_func=get_remote_address, enabled=settings.environment != "test")


@router.post("/password-reset-request", response_model=PasswordResetRequestResponse)
@limiter.limit("3/15 minutes")
async def password_reset_request(
    request: Request,
    reset_data: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Initiate password reset by sending reset code to email."""
    # Check if user exists
    user = await auth_service.get_user_by_email(reset_data.email)
    if not user:
        # Return success anyway to prevent email enumeration
        return {
            "reset_request_status": "success",
            "message": "If the email exists, a reset code has been sent",
        }

    # Generate reset code
    reset_code = generate_otp()

    # Store reset code
    db = auth_service.db
    await db.password_resets.insert_one(
        {
            "email": reset_data.email,
            "reset_code": reset_code,
            "expires_at": get_otp_expiry(),
            "used": False,
            "created_at": datetime.utcnow(),
        }
    )

    # Send reset email
    email_service = get_email_service()
    await email_service.send_password_reset_email(reset_data.email, reset_code)

    return {
        "reset_request_status": "success",
        "message": "If the email exists, a reset code has been sent",
    }


@router.post("/password-reset-verify", response_model=PasswordResetVerifyResponse)
async def password_reset_verify(
    verify_data: PasswordResetVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Verify password reset code."""
    db = auth_service.db

    # Find valid reset code
    reset_record = await db.password_resets.find_one(
        {"email": verify_data.email, "reset_code": verify_data.reset_code, "used": False}
    )

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code",
        )

    if is_otp_expired(reset_record["expires_at"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired",
        )

    # Create temporary token for password reset confirmation
    from app.utils.jwt import create_access_token
    from datetime import timedelta

    temp_token = create_access_token(
        {
            "sub": verify_data.email,
            "type": "password_reset",
            "reset_code": verify_data.reset_code,
        },
        expires_delta=timedelta(minutes=10),
    )

    return {
        "verification_status": "verified",
        "temporary_token": temp_token,
    }


@router.post("/password-reset-confirm", response_model=PasswordResetConfirmResponse)
async def password_reset_confirm(
    confirm_data: PasswordResetConfirmRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Complete password reset with new password."""
    db = auth_service.db

    # Find and validate reset code
    reset_record = await db.password_resets.find_one(
        {
            "email": confirm_data.email,
            "reset_code": confirm_data.reset_code,
            "used": False,
        }
    )

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code",
        )

    if is_otp_expired(reset_record["expires_at"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired",
        )

    # Update user password
    from bson import ObjectId

    user = await db.users.find_one({"email": confirm_data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {"password_hash": hash_password(confirm_data.new_password)}},
    )

    # Mark reset code as used
    await db.password_resets.update_one(
        {"_id": reset_record["_id"]},
        {
            "$set": {
                "used": True,
                "used_at": datetime.utcnow(),
            }
        },
    )

    return {
        "reset_status": "success",
        "message": "Password reset successfully",
    }
