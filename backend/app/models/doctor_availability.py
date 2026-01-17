"""Doctor availability data models."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DoctorAvailabilityCreate(BaseModel):
    """Doctor availability creation request model."""

    doctor_id: str = Field(..., min_length=1)
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: str = Field(..., description="Time in HH:MM format")
    end_time: str = Field(..., description="Time in HH:MM format")
    slot_duration_minutes: int = Field(default=30, ge=15, le=120)
    is_available: bool = Field(default=True)


class DoctorAvailabilityResponse(BaseModel):
    """Doctor availability response model."""

    availability_id: str
    doctor_id: str
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int
    is_available: bool
    created_at: datetime
    updated_at: Optional[datetime]


class AvailableSlotResponse(BaseModel):
    """Available time slot response."""

    date: str
    time: str
    duration_minutes: int
    is_available: bool
