"""Data models for patient management."""
from .patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    MedicalHistoryCreate,
    MedicalHistoryUpdate,
    MedicalHistoryResponse,
    AllergyCreate,
    AllergyResponse,
    InsuranceCreate,
    InsuranceUpdate,
    InsuranceResponse,
    HealthScoreResponse,
)
from .common import EmergencyContact

__all__ = [
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse",
    "MedicalHistoryCreate",
    "MedicalHistoryUpdate",
    "MedicalHistoryResponse",
    "AllergyCreate",
    "AllergyResponse",
    "InsuranceCreate",
    "InsuranceUpdate",
    "InsuranceResponse",
    "HealthScoreResponse",
    "EmergencyContact",
]
