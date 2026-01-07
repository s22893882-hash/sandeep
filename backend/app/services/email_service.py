"""
Email service for sending OTP and password reset emails.
"""
from typing import Dict, Any
from app.config import get_settings

settings = get_settings()


class EmailService:
    """Email service for sending notifications."""

    def __init__(self):
        """Initialize email service."""
        self.mock_mode = settings.email_mock_mode
        self.sent_emails: list[Dict[str, Any]] = []

    async def send_otp_email(self, email: str, otp_code: str) -> bool:
        """Send OTP verification email."""
        if self.mock_mode:
            self._mock_log("OTP", email, {"otp_code": otp_code})
            return True

        # Real email implementation would go here
        # For now, we simulate success
        return True

    async def send_password_reset_email(self, email: str, reset_code: str) -> bool:
        """Send password reset email."""
        if self.mock_mode:
            self._mock_log("Password Reset", email, {"reset_code": reset_code})
            return True

        # Real email implementation would go here
        return True

    def _mock_log(self, email_type: str, email: str, data: Dict[str, Any]) -> None:
        """Log mock email for development/testing."""
        email_log = {
            "type": email_type,
            "to": email,
            "from": settings.email_from_address,
            "data": data,
        }
        self.sent_emails.append(email_log)
        print(f"[MOCK EMAIL] {email_type} to {email}: {data}")

    def get_sent_emails(self) -> list[Dict[str, Any]]:
        """Get all sent emails (for testing)."""
        return self.sent_emails

    def clear_sent_emails(self) -> None:
        """Clear sent emails history (for testing)."""
        self.sent_emails.clear()


email_service = EmailService()


def get_email_service() -> EmailService:
    """Get email service instance."""
    return email_service
