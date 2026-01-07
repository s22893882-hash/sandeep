"""Patient-related data models."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """Allergy severity levels."""

    mild = "mild"
    moderate = "moderate"
    severe = "severe"


class CoverageType(str, Enum):
    """Insurance coverage types."""

    basic = "basic"
    standard = "standard"
    premium = "premium"


class MedicalStatus(str, Enum):
    """Medical condition status."""

    active = "active"
    resolved = "resolved"


# Patient Profile Models
class PatientCreate(BaseModel):
    """Patient registration request model."""

    user_id: str = Field(..., min_length=1)
    date_of_birth: str = Field(..., description="ISO 8601 date format")
    gender: str = Field(..., min_length=1, max_length=20)
    blood_type: str = Field(..., min_length=1, max_length=5)
    height_cm: float = Field(..., gt=0, lt=300)
    weight_kg: float = Field(..., gt=0, lt=500)
    emergency_contact_name: str = Field(..., min_length=1, max_length=100)
    emergency_contact_phone: str = Field(..., min_length=10, max_length=20)


class PatientUpdate(BaseModel):
    """Patient profile update request model."""

    height_cm: Optional[float] = Field(None, gt=0, lt=300)
    weight_kg: Optional[float] = Field(None, gt=0, lt=500)
    emergency_contact_name: Optional[str] = Field(None, min_length=1, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, min_length=10, max_length=20)


class PatientResponse(BaseModel):
    """Patient profile response model."""

    patient_id: str
    user_id: str
    full_name: Optional[str] = None
    date_of_birth: str
    gender: str
    blood_type: str
    height_cm: float
    weight_kg: float
    emergency_contact_name: str
    emergency_contact_phone: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# Medical History Models
class MedicalHistoryCreate(BaseModel):
    """Medical history creation request model."""

    condition_name: str = Field(..., min_length=1, max_length=200)
    diagnosis_date: str = Field(..., description="ISO 8601 date format")
    status: MedicalStatus = Field(default=MedicalStatus.active)
    treatment_notes: Optional[str] = Field(None, max_length=2000)


class MedicalHistoryUpdate(BaseModel):
    """Medical history update request model."""

    status: Optional[MedicalStatus] = None
    treatment_notes: Optional[str] = Field(None, max_length=2000)


class MedicalHistoryResponse(BaseModel):
    """Medical history response model."""

    history_id: str
    patient_id: str
    condition_name: str
    diagnosis_date: str
    status: str
    treatment_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None


# Allergy Models
class AllergyCreate(BaseModel):
    """Allergy creation request model."""

    allergy_name: str = Field(..., min_length=1, max_length=100)
    severity: SeverityLevel
    reaction_description: Optional[str] = Field(None, max_length=500)


class AllergyResponse(BaseModel):
    """Allergy response model."""

    allergy_id: str
    patient_id: str
    allergy_name: str
    severity: str
    reaction_description: Optional[str]
    created_at: datetime


# Insurance Models
class InsuranceCreate(BaseModel):
    """Insurance creation request model."""

    provider_name: str = Field(..., min_length=1, max_length=100)
    policy_number: str = Field(..., min_length=1, max_length=50)
    coverage_type: CoverageType
    expiry_date: str = Field(..., description="ISO 8601 date format")


class InsuranceUpdate(BaseModel):
    """Insurance update request model."""

    provider_name: Optional[str] = Field(None, min_length=1, max_length=100)
    policy_number: Optional[str] = Field(None, min_length=1, max_length=50)
    coverage_type: Optional[CoverageType] = None
    expiry_date: Optional[str] = Field(None, description="ISO 8601 date format")


class InsuranceResponse(BaseModel):
    """Insurance response model."""

    insurance_id: str
    patient_id: str
    provider_name: str
    policy_number: str
    coverage_type: str
    expiry_date: str
    is_expired: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# Health Score Models
class HealthScoreComponents(BaseModel):
    """Health score calculation components."""

    bmi: float
    bmi_component: float
    active_conditions_count: int
    conditions_component: float
    medication_count: int
    medications_component: float
    recent_appointments: int
    appointments_component: float


class HealthScoreResponse(BaseModel):
    """Health score response model."""

    health_score: int = Field(..., ge=0, le=100)
    score_components: HealthScoreComponents
    last_updated: datetime
