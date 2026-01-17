"""Appointment-related data models."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AppointmentStatus(str, Enum):
    """Appointment status enum."""

    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class AppointmentBookRequest(BaseModel):
    """Appointment booking request model."""

    patient_id: str = Field(..., min_length=1)
    doctor_id: str = Field(..., min_length=1)
    appointment_date: str = Field(..., description="ISO 8601 date format (YYYY-MM-DD)")
    appointment_time: str = Field(..., description="Time in HH:MM format")
    reason: str = Field(..., min_length=1, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)


class AppointmentResponse(BaseModel):
    """Appointment response model."""

    appointment_id: str
    patient_id: str
    doctor_id: str
    appointment_date: str
    appointment_time: str
    duration_minutes: int
    reason: str
    notes: Optional[str]
    status: str
    cancellation_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    cancelled_at: Optional[datetime]


class AppointmentDetailResponse(BaseModel):
    """Detailed appointment response with related information."""

    appointment_id: str
    patient_id: str
    doctor_id: str
    patient_name: Optional[str]
    doctor_name: Optional[str]
    appointment_date: str
    appointment_time: str
    duration_minutes: int
    reason: str
    notes: Optional[str]
    status: str
    cancellation_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    cancelled_at: Optional[datetime]


class AppointmentListResponse(BaseModel):
    """Paginated appointment list response."""

    appointments: list[AppointmentResponse]
    total: int
    limit: int
    offset: int


class AppointmentUpdateRequest(BaseModel):
    """Appointment update request model."""

    notes: Optional[str] = Field(None, max_length=1000)
    appointment_date: Optional[str] = Field(None, description="ISO 8601 date format (YYYY-MM-DD)")
    appointment_time: Optional[str] = Field(None, description="Time in HH:MM format")


class AppointmentCancellationRequest(BaseModel):
    """Appointment cancellation request model."""

    cancellation_reason: str = Field(..., min_length=1, max_length=500)


class AppointmentRescheduleRequest(BaseModel):
    """Appointment reschedule request model."""

    new_appointment_date: str = Field(..., description="ISO 8601 date format (YYYY-MM-DD)")
    new_appointment_time: str = Field(..., description="Time in HH:MM format")
