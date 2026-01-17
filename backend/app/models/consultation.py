"""
Consultation-related Pydantic models for Phase 3 Module 2.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ConsultationStatus(str, Enum):
    """Consultation status enum."""
    INITIATED = "initiated"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    PENDING_FOLLOW_UP = "pending-follow-up"
    CANCELLED = "cancelled"


class MessageType(str, Enum):
    """Message type enum."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VIDEO = "video"


class DeliveryStatus(str, Enum):
    """Message delivery status enum."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class PrescriptionStatus(str, Enum):
    """Prescription status enum."""
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    """Document type enum."""
    XRAY = "xray"
    REPORT = "report"
    LAB = "lab"
    SCAN = "scan"
    OTHER = "other"


class FeedbackPriority(str, Enum):
    """Feedback priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Core Consultation Models


class ConsultationStart(BaseModel):
    """Model for starting a consultation."""
    appointment_id: str = Field(..., description="Associated appointment ID")
    patient_id: str = Field(..., description="Patient user ID")
    doctor_id: str = Field(..., description="Doctor user ID")
    reason: Optional[str] = Field(None, description="Reason for consultation")


class ConsultationResponse(BaseModel):
    """Consultation response model."""
    consultation_id: str
    appointment_id: str
    patient_id: str
    doctor_id: str
    status: ConsultationStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[int]
    reason: Optional[str]
    summary: Optional[str]
    session_token: str
    created_at: datetime
    updated_at: datetime


class ConsultationUpdate(BaseModel):
    """Model for updating consultation."""
    status: Optional[ConsultationStatus] = None
    summary: Optional[str] = None


class ConsultationClose(BaseModel):
    """Model for closing a consultation."""
    end_notes: Optional[str] = Field(None, description="Notes when closing consultation")
    duration: Optional[int] = Field(None, description="Duration in minutes")


# Message Models


class MessageCreate(BaseModel):
    """Model for creating a consultation message."""
    sender_id: str = Field(..., description="ID of message sender")
    message_text: str = Field(..., min_length=1, max_length=5000, description="Message content")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Type of message")


class MessageResponse(BaseModel):
    """Message response model."""
    message_id: str
    consultation_id: str
    sender_id: str
    message_text: str
    message_type: MessageType
    file_url: Optional[str] = None
    timestamp: datetime
    delivery_status: DeliveryStatus
    is_read: bool
    read_at: Optional[datetime]


class MessageQuery(BaseModel):
    """Model for querying messages."""
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


# Prescription Models


class Medication(BaseModel):
    """Individual medication in prescription."""
    medication_name: str = Field(..., description="Name of medication")
    dosage: str = Field(..., description="Dosage amount")
    frequency: str = Field(..., description="Frequency of intake")
    duration: str = Field(..., description="Duration of treatment")
    instructions: str = Field(..., description="Special instructions")


class PrescriptionCreate(BaseModel):
    """Model for creating prescription."""
    medications: List[Medication] = Field(..., description="List of medications")
    instructions: Optional[str] = Field(None, description="General instructions")


class PrescriptionResponse(BaseModel):
    """Prescription response model."""
    prescription_id: str
    consultation_id: str
    doctor_id: str
    patient_id: str
    medications: List[Medication]
    instructions: Optional[str]
    qr_code: str
    prescription_status: PrescriptionStatus
    issued_date: datetime
    expiry_date: datetime
    created_at: datetime


# Clinical Notes Models


class Vitals(BaseModel):
    """Patient vitals."""
    blood_pressure: Optional[str] = Field(None, description="Blood pressure (e.g., 120/80)")
    heart_rate: Optional[int] = Field(None, ge=30, le=200, description="Heart rate in BPM")
    temperature: Optional[float] = Field(None, ge=35.0, le=45.0, description="Temperature in Celsius")
    weight: Optional[float] = Field(None, ge=0, le=500, description="Weight in kg")


class ClinicalNotesCreate(BaseModel):
    """Model for creating clinical notes."""
    notes_text: str = Field(..., min_length=1, max_length=10000, description="Clinical notes content")
    vitals: Optional[Vitals] = Field(None, description="Patient vitals")
    diagnosis: Optional[str] = Field(None, max_length=1000, description="Diagnosis")
    treatment_plan: Optional[str] = Field(None, max_length=2000, description="Treatment plan")


class ClinicalNotesResponse(BaseModel):
    """Clinical notes response model."""
    notes_id: str
    consultation_id: str
    doctor_id: str
    notes_text: str
    vitals: Optional[Vitals]
    diagnosis: Optional[str]
    treatment_plan: Optional[str]
    follow_up_required: bool
    version: int
    created_at: datetime
    updated_at: datetime


# Document Management Models


class DocumentCreate(BaseModel):
    """Model for creating document attachment."""
    document_type: DocumentType = Field(..., description="Type of document")
    description: str = Field(..., max_length=500, description="Document description")


class DocumentResponse(BaseModel):
    """Document response model."""
    document_id: str
    consultation_id: str
    document_url: str
    document_type: DocumentType
    file_name: str
    file_size: int
    uploaded_by: str
    description: str
    is_scanned: bool
    created_at: datetime
    updated_at: datetime


# Follow-up Models


class FollowUpCreate(BaseModel):
    """Model for creating follow-up consultation."""
    follow_up_date: datetime = Field(..., description="Scheduled follow-up date")
    reason: str = Field(..., max_length=500, description="Reason for follow-up")
    priority: FeedbackPriority = Field(default=FeedbackPriority.MEDIUM, description="Priority level")


class FollowUpResponse(BaseModel):
    """Follow-up response model."""
    follow_up_id: str
    original_consultation_id: str
    follow_up_consultation_id: Optional[str]
    scheduled_date: datetime
    reason: str
    priority: FeedbackPriority
    status: str
    created_at: datetime


# Feedback Models


class FeedbackCreate(BaseModel):
    """Model for creating consultation feedback."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Feedback text")
    would_recommend: bool = Field(..., description="Would recommend doctor")
    anonymous: bool = Field(default=False, description="Anonymous feedback")


class FeedbackResponse(BaseModel):
    """Feedback response model."""
    feedback_id: str
    consultation_id: str
    patient_id: str
    rating: int
    feedback_text: Optional[str]
    would_recommend: bool
    anonymous: bool
    created_at: datetime
    updated_at: datetime


# Video Token Models


class VideoTokenCreate(BaseModel):
    """Model for creating video call token."""
    participant_type: str = Field(..., pattern="^(doctor|patient)$", description="Type of participant")
    session_duration: int = Field(default=60, ge=5, le=180, description="Session duration in minutes")


class VideoTokenResponse(BaseModel):
    """Video token response model."""
    video_token: str
    channel_name: str
    rtc_uid: str
    expires_at: datetime


# Consultation Query Models


class ConsultationQuery(BaseModel):
    """Model for querying consultations."""
    status: Optional[str] = Field(None, pattern="^(all|active|completed)$")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class DoctorConsultationQuery(BaseModel):
    """Model for doctor's consultation queries."""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    patient_name: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(all|active|completed)$")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)