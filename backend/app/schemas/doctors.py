"""
Doctor management schemas for API validation and response models.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class UserResponse(BaseModel):
    user_id: str
    email: str
    phone: str
    name: str
    role: UserRole
    is_active: bool

    class Config:
        orm_mode = True


class Qualification(BaseModel):
    degree: str
    institution: str
    year: int
    field: str

    class Config:
        orm_mode = True


class WorkingHours(BaseModel):
    start: str  # "HH:MM" format
    end: str  # "HH:MM" format

    @validator("start", "end")
    def validate_time_format(cls, v):
        """Validate time format is HH:MM."""
        try:
            hours, minutes = map(int, v.split(":"))
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError("Invalid time format")
            return v
        except (ValueError, AttributeError):
            raise ValueError("Time must be in HH:MM format")

    class Config:
        orm_mode = True


class SpecializationItem(BaseModel):
    specialization_name: str
    expertise_level: str  # beginner/intermediate/expert

    @validator("expertise_level")
    def validate_expertise_level(cls, v):
        """Validate expertise level."""
        if v not in ["beginner", "intermediate", "expert"]:
            raise ValueError("Expertise level must be beginner, intermediate, or expert")
        return v

    class Config:
        orm_mode = True


class AvailableSlot(BaseModel):
    start_time: str
    end_time: str

    class Config:
        orm_mode = True


class DoctorRegistrationRequest(BaseModel):
    """Request schema for doctor registration/onboarding."""

    license_number: str = Field(..., min_length=1)
    license_expiry: datetime
    specialization: List[SpecializationItem]
    qualifications: List[Qualification]
    clinic_address: str = Field(..., min_length=1)
    clinic_phone: str = Field(..., min_length=1)
    consultation_fee: float = Field(..., gt=0)
    working_hours: Dict[str, WorkingHours]
    bio: Optional[str] = ""
    languages: Optional[List[str]] = []
    license_document_url: Optional[str] = None

    @validator("consultation_fee")
    def validate_fee(cls, v):
        """Validate consultation fee is positive."""
        if v <= 0:
            raise ValueError("Consultation fee must be greater than 0")
        return v

    @validator("specialization")
    def validate_specialization(cls, v):
        """Ensure at least one specialization is provided."""
        if not v:
            raise ValueError("At least one specialization is required")
        return v

    @validator("license_expiry")
    def validate_license_expiry(cls, v):
        """Validate license hasn't expired."""
        if v < datetime.utcnow():
            raise ValueError("License has expired")
        return v

    class Config:
        orm_mode = True


class DoctorProfileResponse(BaseModel):
    """Response schema for doctor profile."""

    doctor_id: str
    user: UserResponse
    license_number: str
    license_expiry: datetime
    specialization: List[SpecializationItem]
    qualifications: List[Qualification]
    clinic_address: str
    clinic_phone: str
    consultation_fee: float
    is_verified: bool
    verification_date: Optional[datetime]
    average_rating: float
    review_count: int
    working_hours: Dict[str, WorkingHours]
    bio: str
    languages: List[str]
    availability_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DoctorListResponse(BaseModel):
    """Response schema for doctor listing (public info only)."""

    doctor_id: str
    user: UserResponse
    specializations: List[str]
    clinic_address: str
    consultation_fee: float
    average_rating: float
    review_count: int
    availability_status: str
    is_verified: bool
    created_at: datetime

    class Config:
        orm_mode = True


class DoctorStatistics(BaseModel):
    """Statistics for a doctor's performance."""

    total_appointments: int
    completed_appointments: int
    avg_rating: float
    specializations: List[str]
    recent_reviews: List[Dict[str, Any]]
    appointment_duration_avg: int

    class Config:
        orm_mode = True


class WorkingHoursUpdate(BaseModel):
    """Schema for updating working hours."""

    working_hours: Dict[str, WorkingHours]
    is_available_weekends: bool = False

    class Config:
        orm_mode = True


class AvailabilityStatusUpdate(BaseModel):
    """Schema for updating doctor availability status."""

    status: str  # available/on-leave/unavailable
    reason: Optional[str] = None
    return_date: Optional[datetime] = None

    @validator("status")
    def validate_status(cls, v):
        """Validate availability status."""
        if v not in ["available", "on-leave", "unavailable"]:
            raise ValueError("Status must be available, on-leave, or unavailable")
        return v

    class Config:
        orm_mode = True


class VerificationRequest(BaseModel):
    """Schema for doctor verification."""

    verified: bool
    rejection_reason: Optional[str] = None

    class Config:
        orm_mode = True


class RatingResponse(BaseModel):
    """Response schema for doctor ratings."""

    average_rating: float
    review_count: int
    reviews: List[Dict[str, Any]]

    class Config:
        orm_mode = True


class AppointmentResponse(BaseModel):
    """Schema for doctor appointments."""

    appointment_id: str
    patient_id: str
    patient_name: str
    date: datetime
    start_time: str
    end_time: str
    status: str

    class Config:
        orm_mode = True


class DoctorSearchFilters(BaseModel):
    """Filters for searching doctors."""

    specialization: Optional[str] = None
    rating_min: Optional[float] = None
    consultation_fee_max: Optional[float] = None
    location: Optional[str] = None
    is_verified: Optional[bool] = None
    availability_status: Optional[str] = None
