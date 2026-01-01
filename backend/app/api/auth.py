"""Authentication API routes."""
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.config import get_settings
from app.logging import get_logger
from app.models import Token, TokenPayload, LoginRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()
logger = get_logger(__name__)

# Security
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify and decode JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning("Token verification failed", exc_info=e)
        raise credentials_exception


# Mock user database (in production, use real database)
users_db = {
    1: {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",  # In production, this should be hashed
        "is_active": True,
    }
}


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest) -> Token:
    """
    Authenticate user and return access token.

    - **email**: User email
    - **password**: User password
    """
    logger.info("Login attempt", extra={"email": login_data.email})

    # Find user by email
    user = None
    for u in users_db.values():
        if u["email"] == login_data.email:
            user = u
            break

    # Verify user exists and password matches (in production, use password hashing)
    if not user or user["password"] != login_data.password:
        logger.warning(
            "Login failed - invalid credentials",
            extra={"email": login_data.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.get("is_active", True):
        logger.warning("Login failed - inactive user", extra={"email": login_data.email})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user["id"])},
    )

    logger.info("Login successful", extra={"user_id": user["id"]})

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/verify", response_model=UserResponse)
async def verify_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserResponse:
    """Verify access token and return user information."""
    try:
        payload = verify_token(credentials)
        user_id = int(payload.get("sub"))

        logger.info("Token verification", extra={"user_id": user_id})

        user = users_db.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            is_active=user["is_active"],
        )

    except Exception as e:
        logger.error("Token verification failed", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Token:
    """Refresh access token."""
    try:
        payload = verify_token(credentials)
        user_id = int(payload.get("sub"))

        logger.info("Token refresh", extra={"user_id": user_id})

        user = users_db.get(user_id)
        if not user or not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user["id"])},
        )

        logger.info("Token refreshed successfully", extra={"user_id": user_id})

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except Exception as e:
        logger.error("Token refresh failed", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
