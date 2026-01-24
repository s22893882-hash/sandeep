"""Prescription-related data models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PrescriptionStatus(str, Enum):
    """Prescription status options."""

    active = "active"
    expired = "expired"
    used = "used"
    cancelled = "cancelled"


class Medication(BaseModel):
    """Medication details model."""

    medication_name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., min_length=1, max_length=100)
    instructions: Optional[str] = Field(None, max_length=500)


class PrescriptionCreate(BaseModel):
    """Prescription creation request model."""

    medications: List[Medication] = Field(..., min_length=1)
    notes: Optional[str] = Field(None, max_length=1000)


class PrescriptionResponse(BaseModel):
    """Prescription response model."""

    prescription_id: str
    consultation_id: str
    doctor_id: str
    patient_id: str
    medications: List[Medication]
    notes: Optional[str] = None
    qr_code: str
    prescription_status: str
    issued_date: datetime
    expiry_date: datetime
    is_expired: bool = False
    created_at: datetime


class PrescriptionsListResponse(BaseModel):
    """Prescriptions list response model."""

    prescriptions: List[PrescriptionResponse]
    total_count: int
