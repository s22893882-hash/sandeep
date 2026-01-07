"""Appointment-related data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AppointmentStatus(str, Enum):
    """Appointment status levels."""

    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    rescheduled = "rescheduled"


class AppointmentSlot(BaseModel):
    """Appointment slot model."""

    doctor_id: str
    date: str  # ISO 8601 date format
    time: str  # HH:MM format
    available: bool = True
    booked_by: Optional[str] = None


class AppointmentBase(BaseModel):
    """Base appointment model."""

    patient_id: str
    doctor_id: str
    appointment_date: str  # ISO 8601 date format
    time_slot: str  # HH:MM format
    notes: Optional[str] = Field(None, max_length=1000)


class AppointmentCreate(AppointmentBase):
    """Appointment creation request model."""

    pass


class AppointmentUpdate(BaseModel):
    """Appointment update request model."""

    appointment_date: Optional[str] = None
    time_slot: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)


class AppointmentResponse(AppointmentBase):
    """Appointment response model."""

    appointment_id: str
    status: AppointmentStatus
    reminder_sent: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class RescheduleHistory(BaseModel):
    """Reschedule history model."""

    appointment_id: str
    old_date: str
    old_time: str
    new_date: str
    new_time: str
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DoctorStats(BaseModel):
    """Doctor appointment statistics."""

    doctor_id: str
    total_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    upcoming_appointments: int
