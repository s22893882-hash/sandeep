"""
User-related Pydantic models.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """User registration model."""

    password: str = Field(..., min_length=8, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None


class UserLogin(BaseModel):
    """User login model."""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User profile update model."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)


class UserResponse(BaseModel):
    """User response model."""

    user_id: str
    email: str
    full_name: str
    phone_number: Optional[str]
    date_of_birth: Optional[datetime]
    address: Optional[str]
    profile_photo_url: Optional[str]
    user_type: str
    verification_status: str
    created_at: datetime
    updated_at: Optional[datetime]


class UserRegisterResponse(BaseModel):
    """User registration response model."""

    user_id: str
    email: str
    verification_status: str


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response model."""

    access_token: str
    token_type: str = "bearer"


class AccountDeletionRequest(BaseModel):
    """Account deletion request model."""

    password: str


class AccountDeletionResponse(BaseModel):
    """Account deletion response model."""

    deletion_status: str
    message: str
