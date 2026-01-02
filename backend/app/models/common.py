"""Common model definitions."""
from pydantic import BaseModel, Field


class EmergencyContact(BaseModel):
    """Emergency contact information."""

    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
