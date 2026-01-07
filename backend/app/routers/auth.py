"""
Authentication routes for user registration, login, OTP verification.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings
from app.models.otp import OTPVerifyRequest, OTPVerifyResponse
from app.models.user import (
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserRegisterResponse,
)
from app.services.auth_service import AuthService, get_auth_service

settings = get_settings()
router = APIRouter(prefix="/api/users", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address, enabled=settings.environment != "test")


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    """Register a new user account."""
    try:
        result = await auth_service.register_user(user_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user",
        ) from e


@router.post("/verify-otp", response_model=OTPVerifyResponse)
async def verify_otp(otp_data: OTPVerifyRequest, auth_service: AuthService = Depends(get_auth_service)):
    """Verify OTP code for email verification."""
    try:
        result = await auth_service.verify_otp(otp_data.email, otp_data.otp_code)
        if result["verification_status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"],
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP",
        ) from e


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/15 minutes")
async def login(
    request: Request,
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user and return JWT tokens."""
    try:
        result = await auth_service.login_user(login_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate user",
        ) from e


@router.post("/refresh-token", response_model=RefreshTokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    try:
        result = await auth_service.refresh_token(token_data.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token",
        ) from e
