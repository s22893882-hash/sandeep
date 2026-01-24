"""Clinical notes-related data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Vitals(BaseModel):
    """Patient vitals model."""

    blood_pressure: Optional[str] = Field(None, max_length=20)
    heart_rate: Optional[int] = Field(None, ge=0, le=300)
    temperature: Optional[float] = Field(None, ge=30.0, le=45.0)
    weight: Optional[float] = Field(None, gt=0, lt=500)
    height: Optional[float] = Field(None, gt=0, lt=300)
    respiratory_rate: Optional[int] = Field(None, ge=0, le=100)
    oxygen_saturation: Optional[float] = Field(None, ge=0, le=100)


class ClinicalNotesCreate(BaseModel):
    """Clinical notes creation request model."""

    notes_text: str = Field(..., min_length=1, max_length=10000)
    vitals: Optional[Vitals] = None
    diagnosis: Optional[str] = Field(None, max_length=500)
    treatment_plan: Optional[str] = Field(None, max_length=5000)


class ClinicalNotesUpdate(BaseModel):
    """Clinical notes update request model."""

    notes_text: Optional[str] = Field(None, max_length=10000)
    vitals: Optional[Vitals] = None
    diagnosis: Optional[str] = Field(None, max_length=500)
    treatment_plan: Optional[str] = Field(None, max_length=5000)


class ClinicalNotesResponse(BaseModel):
    """Clinical notes response model."""

    notes_id: str
    consultation_id: str
    doctor_id: str
    notes_text: str
    vitals: Optional[Vitals] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    version: int = 1
    created_at: datetime
    updated_at: Optional[datetime] = None
