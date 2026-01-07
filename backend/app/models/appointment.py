"""Appointment-related data models for Phase 3."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AppointmentStatus(str, Enum):
    """Appointment status enum."""

    scheduled = "scheduled"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"
    rescheduled = "rescheduled"


class RefundStatus(str, Enum):
    """Refund status enum."""

    pending = "pending"
    processed = "processed"
    failed = "failed"
    not_applicable = "not_applicable"


class ReminderStatus(str, Enum):
    """Reminder status enum."""

    scheduled = "scheduled"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


class ReminderChannel(str, Enum):
    """Reminder channel enum."""

    email = "email"
    sms = "sms"
    push = "push"


# Core Appointment Models
class AppointmentCreate(BaseModel):
    """Appointment creation request model."""

    doctor_id: str = Field(..., min_length=1, description="Doctor's user ID")
    appointment_date: str = Field(..., description="ISO 8601 date format YYYY-MM-DD")
    appointment_time: str = Field(..., description="ISO 8601 time format HH:MM")
    duration_minutes: int = Field(default=30, ge=15, le=180, description="Appointment duration in minutes")
    notes: Optional[str] = Field(None, max_length=500, description="Patient notes for the appointment")
    consultation_type: str = Field(default="general", description="Type of consultation")


class AppointmentUpdate(BaseModel):
    """Appointment update request model."""

    appointment_date: Optional[str] = Field(None, description="ISO 8601 date format YYYY-MM-DD")
    appointment_time: Optional[str] = Field(None, description="ISO 8601 time format HH:MM")
    duration_minutes: Optional[int] = Field(None, ge=15, le=180)
    notes: Optional[str] = Field(None, max_length=500)
    status: Optional[AppointmentStatus] = None


class AppointmentResponse(BaseModel):
    """Appointment response model."""

    appointment_id: str
    patient_id: str
    doctor_id: str
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    appointment_date: str
    appointment_time: str
    duration_minutes: int
    status: str
    notes: Optional[str]
    consultation_type: str
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    is_cancelled: bool
    cancellation_reason: Optional[str]
    refund_status: Optional[str]
    refund_amount: Optional[float]
    refund_processed_at: Optional[datetime]
    reminders_sent: List[str] = []
    consultation_notes: Optional[str] = None


# Availability Models
class TimeSlot(BaseModel):
    """Time slot model."""

    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    is_available: bool
    appointment_id: Optional[str] = None


class DayAvailability(BaseModel):
    """Day availability model."""

    date: str  # YYYY-MM-DD format
    slots: List[TimeSlot]
    is_working_day: bool


class DoctorAvailabilityResponse(BaseModel):
    """Doctor availability response model."""

    doctor_id: str
    doctor_name: Optional[str]
    date_range: Dict[str, str]  # {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    availability: List[DayAvailability]
    total_available_slots: int
    response_time_ms: int


# Rescheduling Models
class RescheduleRequest(BaseModel):
    """Appointment reschedule request model."""

    new_date: str = Field(..., description="ISO 8601 date format YYYY-MM-DD")
    new_time: str = Field(..., description="ISO 8601 time format HH:MM")
    reason: Optional[str] = Field(None, max_length=200)


class RescheduleResponse(BaseModel):
    """Reschedule response model."""

    old_appointment: AppointmentResponse
    new_appointment: AppointmentResponse
    reschedule_id: str
    rescheduled_at: datetime
    refund_adjustment: Optional[float] = 0.0


class BulkRescheduleRequest(BaseModel):
    """Bulk reschedule request model."""

    doctor_id: str
    target_date: str
    new_time_slots: List[Dict[str, str]]  # [{"appointment_id": "xxx", "new_time": "HH:MM"}]
    reason: Optional[str] = Field(None, max_length=200)


# Cancellation Models
class CancellationRequest(BaseModel):
    """Appointment cancellation request model."""

    reason: Optional[str] = Field(None, max_length=200, description="Reason for cancellation")


class CancellationResponse(BaseModel):
    """Cancellation response model."""

    appointment_id: str
    status: str
    refund_status: str
    refund_amount: float
    refund_percentage: float
    cancellation_reason: Optional[str]
    cancelled_at: datetime
    refund_policy: str


# Reminder Models
class ReminderCreate(BaseModel):
    """Reminder creation request model."""

    appointment_id: str
    reminder_time: str = Field(..., description="ISO 8601 datetime format")
    channel: ReminderChannel
    message: Optional[str] = Field(None, max_length=200)


class ReminderResponse(BaseModel):
    """Reminder response model."""

    reminder_id: str
    appointment_id: str
    reminder_time: datetime
    channel: str
    status: str
    message: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime


# Statistics Models
class DoctorStatsResponse(BaseModel):
    """Doctor statistics response model."""

    doctor_id: str
    doctor_name: Optional[str]
    period: Dict[str, str]  # {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    total_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    no_show_appointments: int
    rescheduled_appointments: int
    average_appointment_duration: float
    total_revenue: float
    cancellation_rate: float
    completion_rate: float
    most_common_consultation_type: str
    busiest_day: str
    peak_hour: str


class ConflictDetectionResponse(BaseModel):
    """Conflict detection response model."""

    conflict_found: bool
    conflicting_appointments: List[Dict[str, Any]]
    suggested_alternatives: List[Dict[str, Any]]
    checked_time_range: Dict[str, str]
    analysis_time_ms: int


# Calendar Models
class CalendarEvent(BaseModel):
    """Calendar event model."""

    appointment_id: str
    title: str
    date: str
    start_time: str
    end_time: str
    status: str
    patient_name: Optional[str] = None
    consultation_type: str
    notes: Optional[str] = None


class CalendarViewResponse(BaseModel):
    """Calendar view response model."""

    doctor_id: str
    doctor_name: Optional[str]
    date_range: Dict[str, str]
    events: List[CalendarEvent]
    total_events: int
    view_generation_time_ms: int


# Appointment Slot Management
class AppointmentSlotCreate(BaseModel):
    """Appointment slot creation request model."""

    doctor_id: str
    date: str = Field(..., description="ISO 8601 date format YYYY-MM-DD")
    start_time: str = Field(..., description="ISO 8601 time format HH:MM")
    end_time: str = Field(..., description="ISO 8601 time format HH:MM")
    is_available: bool = True
    slot_type: str = Field(default="general", description="Type of slot")


class AppointmentSlotResponse(BaseModel):
    """Appointment slot response model."""

    slot_id: str
    doctor_id: str
    date: str
    start_time: str
    end_time: str
    is_available: bool
    slot_type: str
    created_at: datetime
    updated_at: Optional[datetime]


class WorkingHoursUpdate(BaseModel):
    """Working hours update model."""

    doctor_id: str
    working_hours: Dict[str, List[str]]  # {"monday": ["09:00-17:00"], "tuesday": ["09:00-17:00"], etc.}


# Analytics Models
class AppointmentAnalytics(BaseModel):
    """Appointment analytics model."""

    total_appointments: int
    appointments_by_status: Dict[str, int]
    appointments_by_day: Dict[str, int]
    average_booking_lead_time: float  # hours between booking and appointment
    peak_booking_hours: List[str]
    most_active_doctors: List[Dict[str, Any]]
    cancellation_reasons: Dict[str, int]


class RescheduleHistoryResponse(BaseModel):
    """Reschedule history response model."""

    history_id: str
    appointment_id: str
    old_date: str
    old_time: str
    new_date: str
    new_time: str
    rescheduled_by: str
    reason: Optional[str]
    rescheduled_at: datetime
