"""
OTP-related Pydantic models.
"""
from pydantic import BaseModel, EmailStr, Field


class OTPVerifyRequest(BaseModel):
    """OTP verification request model."""

    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)


class OTPVerifyResponse(BaseModel):
    """OTP verification response model."""

    verification_status: str
    message: str
