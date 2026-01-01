"""User and doctor data models for the doctor management system."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from app.models.base import BaseDocument


class UserRole(str, Enum):
    """User roles in the system."""

    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class Qualification(BaseDocument):
    """Doctor's qualification information."""

    degree: str
    institution: str
    year: int
    field: str


class WorkingHours(BaseDocument):
    """Doctor's working hours for a day."""

    start: str  # "HH:MM" format
    end: str  # "HH:MM" format


class Specialization(BaseDocument):
    """Doctor's specialization details."""

    name: str
    expertise_level: str  # beginner/intermediate/expert


class User(BaseDocument):
    """User model."""

    email: str
    phone: str
    name: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"


class DoctorProfile(BaseDocument):
    """Doctor profile model."""

    user_id: str  # References User
    license_number: str
    license_expiry: datetime
    specializations: List[Specialization] = []
    qualifications: List[Qualification] = []
    clinic_address: str
    clinic_phone: str
    consultation_fee: float
    working_hours: dict = {}  # dict of day -> WorkingHours
    is_verified: bool = False
    verification_date: Optional[datetime] = None
    average_rating: float = 0.0
    review_count: int = 0
    availability_status: str = "available"  # available/on-leave/unavailable
    bio: str = ""
    languages: List[str] = []
    license_document_url: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "doctors"


class Appointment(BaseDocument):
    """Appointment model."""

    doctor_id: str
    patient_id: str
    date: datetime
    start_time: str  # "HH:MM"
    end_time: str  # "HH:MM"
    status: str  # scheduled/completed/cancelled/no-show
    consultation_notes: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "appointments"


class Review(BaseDocument):
    """Patient review/rating for doctor."""

    doctor_id: str
    patient_id: str
    patient_name: str
    rating: int  # 1-5
    comment: str
    date: datetime = datetime.utcnow()

    class Settings:
        name = "reviews"
