"""
Password reset-related Pydantic models.
"""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    """Password reset request model."""

    email: EmailStr


class PasswordResetVerifyRequest(BaseModel):
    """Password reset verification request model."""

    email: EmailStr
    reset_code: str = Field(..., min_length=6, max_length=6)


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation model."""

    email: EmailStr
    reset_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordResetRequestResponse(BaseModel):
    """Password reset request response model."""

    reset_request_status: str
    message: str


class PasswordResetVerifyResponse(BaseModel):
    """Password reset verify response model."""

    verification_status: str
    temporary_token: Optional[str]


class PasswordResetConfirmResponse(BaseModel):
    """Password reset confirm response model."""

    reset_status: str
    message: str
