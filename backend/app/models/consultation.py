"""Consultation-related data models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ConsultationStatus(str, Enum):
    """Consultation status levels."""

    pending = "pending"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class ConsultationMessageType(str, Enum):
    """Message types."""

    text = "text"
    image = "image"
    document = "document"
    system = "system"


class ConsultationMessage(BaseModel):
    """Consultation message model."""

    message_id: str
    consultation_id: str
    sender_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: ConsultationMessageType = ConsultationMessageType.text


class Prescription(BaseModel):
    """Prescription model."""

    prescription_id: str
    consultation_id: str
    doctor_id: str
    patient_id: str
    medications: List[dict]  # List of {name, dosage, duration, instructions}
    issued_at: datetime = Field(default_factory=datetime.utcnow)


class ClinicalNote(BaseModel):
    """Clinical note model."""

    note_id: str
    consultation_id: str
    doctor_id: str
    notes: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConsultationDocument(BaseModel):
    """Consultation document model."""

    document_id: str
    consultation_id: str
    document_url: str
    file_type: str
    uploaded_by: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConsultationFeedback(BaseModel):
    """Consultation feedback model."""

    consultation_id: str
    patient_id: str
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = Field(None, max_length=1000)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConsultationBase(BaseModel):
    """Base consultation model."""

    patient_id: str
    doctor_id: str
    appointment_id: Optional[str] = None


class ConsultationCreate(ConsultationBase):
    """Consultation creation request model."""

    pass


class ConsultationResponse(ConsultationBase):
    """Consultation response model."""

    consultation_id: str
    status: ConsultationStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # in minutes
    created_at: datetime
    updated_at: Optional[datetime] = None
