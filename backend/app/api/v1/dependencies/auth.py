"""
Authentication and authorization dependencies for secure API endpoints.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token
from app.models.user import UserRole

security = HTTPBearer(scheme_name="JWT", auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """
    Decode and verify JWT token from request headers.

    This dependency extracts the token from the Authorization header,
    validates its signature and expiration, then returns the user data
    contained within the token payload.

    Args:
        credentials: JWT bearer token from Authorization header

    Returns:
        dict: Decoded user data including user_id, role, and email

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not credentials:
        # Token not provided - return None for optional auth endpoints
        return None

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user data from token payload
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email", ""),
        "role": payload.get("role", UserRole.PATIENT),
        "token_exp": payload.get("exp"),
    }


async def get_current_active_doctor(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Validate that the current user is an active doctor.

    This dependency checks that the user has the DOCTOR role and
    enforces authentication requirements.

    Args:
        current_user: User data from token validation

    Returns:
        dict: User data if user is an active doctor

    Raises:
        HTTPException: If user is not authenticated or not a doctor
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if current_user["role"] != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor privileges required",
        )

    # Verify token hasn't expired
    if current_user.get("token_exp") and datetime.utcnow().timestamp() > current_user["token_exp"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user


async def get_current_admin(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Validate that the current user is an admin.

    This dependency checks that the user has the ADMIN role,
    enforcing admin privileges for sensitive operations.

    Args:
        current_user: User data from token validation

    Returns:
        dict: User data if user is an admin

    Raises:
        HTTPException: If user is not authenticated or not an admin
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    # Verify token hasn't expired
    if current_user.get("token_exp") and datetime.utcnow().timestamp() > current_user["token_exp"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user


async def optional_authentication(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """
    Optionally authenticate a user without enforcing authentication.

    This dependency validates the token if provided, but doesn't
    require authentication for the endpoint.

    Args:
        credentials: JWT bearer token from Authorization header

    Returns:
        dict: User data if token is valid, None otherwise
    """
    if not credentials:
        return None

    payload = verify_token(credentials.credentials)
    if payload is None:
        return None

    return {"user_id": payload.get("sub"), "email": payload.get("email", ""), "role": payload.get("role", UserRole.PATIENT)}
