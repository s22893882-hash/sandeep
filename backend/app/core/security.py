"""
Security utilities for JWT authentication and password hashing.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.models.user import UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_verification_token(doctor_id: str) -> str:
    """Create verification token for doctor."""
    return create_access_token(data={"doctor_id": doctor_id, "type": "verification"}, expires_delta=timedelta(days=7))


def get_required_roles(endpoint_path: str) -> list:
    """Get required roles for endpoints."""
    if "/admin" in endpoint_path:
        return [UserRole.ADMIN]
    if "/api/doctors/me" in endpoint_path:
        return [UserRole.DOCTOR]
    return [UserRole.PATIENT, UserRole.DOCTOR, UserRole.ADMIN]
