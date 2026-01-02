"""
OTP generation and verification utilities.
"""
import random
from datetime import datetime, timedelta

from app.config import get_settings

settings = get_settings()


def generate_otp() -> str:
    """Generate a 6-digit OTP code."""
    return "".join([str(random.randint(0, 9)) for _ in range(settings.otp_length)])


def is_otp_expired(expires_at: datetime) -> bool:
    """Check if OTP has expired."""
    return datetime.utcnow() > expires_at


def get_otp_expiry() -> datetime:
    """Get OTP expiration time."""
    return datetime.utcnow() + timedelta(minutes=settings.otp_expire_minutes)
