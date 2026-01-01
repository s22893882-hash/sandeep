"""
Simple FastAPI application for demonstration.
"""


def get_app_version():
    """Return the application version."""
    return "1.0.0"


def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": get_app_version(),
        "environment": "test",
    }


def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers."""
    return a + b


def calculate_product(a: int, b: int) -> int:
    """Calculate product of two numbers."""
    return a * b


def validate_email(email: str) -> bool:
    """Validate email format."""
    return "@" in email and "." in email.split("@")[1]


class User:
    """User model."""

    def __init__(self, user_id: int, email: str, username: str):
        self.id = user_id
        self.email = email
        self.username = username
        self.is_active = True

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "is_active": self.is_active,
        }

    def deactivate(self):
        """Deactivate the user."""
        self.is_active = False

    def activate(self):
        """Activate the user."""
        self.is_active = True
