"""Consultation-related data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ConsultationStatus(str, Enum):
    """Consultation status options."""

    initiated = "initiated"
    in_progress = "in-progress"
    completed = "completed"
    cancelled = "cancelled"


class ConsultationCreate(BaseModel):
    """Consultation creation request model."""

    appointment_id: str = Field(..., min_length=1)
    patient_id: str = Field(..., min_length=1)
    doctor_id: str = Field(..., min_length=1)


class ConsultationUpdate(BaseModel):
    """Consultation update request model."""

    status: Optional[ConsultationStatus] = None
    end_notes: Optional[str] = Field(None, max_length=2000)


class ConsultationResponse(BaseModel):
    """Consultation response model."""

    consultation_id: str
    appointment_id: str
    patient_id: str
    patient_name: Optional[str] = None
    doctor_id: str
    doctor_name: Optional[str] = None
    specialization: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    session_token: Optional[str] = None
    messages_count: int = 0
    prescriptions_count: int = 0
    documents_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None


class ConsultationListResponse(BaseModel):
    """Consultation list item response model."""

    consultation_id: str
    doctor_id: str
    doctor_name: Optional[str] = None
    specialization: Optional[str] = None
    patient_id: str
    patient_name: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    has_prescriptions: bool = False
    has_clinical_notes: bool = False
    feedback_rating: Optional[int] = None
    created_at: datetime


class ConsultationHistoryResponse(BaseModel):
    """Consultation history list response model."""

    consultations: list[ConsultationListResponse]
    total_count: int
    limit: int
    offset: int


class ConsultationCloseRequest(BaseModel):
    """Request model for closing a consultation."""

    end_notes: str = Field(..., min_length=1, max_length=2000)


class ConsultationCloseResponse(BaseModel):
    """Response model for closing a consultation."""

    consultation_id: str
    status: str
    end_time: datetime
    duration_minutes: int
    completion_summary: str


class StatusUpdateRequest(BaseModel):
    """Request model for updating consultation status."""

    status: ConsultationStatus
