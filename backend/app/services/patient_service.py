"""Patient management business logic."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.patient import (
    PatientCreate,
    PatientUpdate,
    MedicalHistoryCreate,
    MedicalHistoryUpdate,
    AllergyCreate,
    InsuranceCreate,
    InsuranceUpdate,
)
from app.database import generate_id


class PatientService:
    """Service for managing patient data."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def register_patient(self, patient_data: PatientCreate) -> Dict[str, Any]:
        """Register a new patient profile."""
        # Check if patient with this user_id already exists
        existing = await self.db.patients.find_one({"user_id": patient_data.user_id})
        if existing:
            raise ValueError("Patient profile already exists for this user")

        # Create patient record
        patient_id = generate_id("PT")
        now = datetime.utcnow()
        patient_doc = {
            "patient_id": patient_id,
            "user_id": patient_data.user_id,
            "date_of_birth": patient_data.date_of_birth,
            "gender": patient_data.gender,
            "blood_type": patient_data.blood_type,
            "height_cm": patient_data.height_cm,
            "weight_kg": patient_data.weight_kg,
            "emergency_contact_name": patient_data.emergency_contact_name,
            "emergency_contact_phone": patient_data.emergency_contact_phone,
            "full_name": None,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
        }

        await self.db.patients.insert_one(patient_doc)

        return {
            "patient_id": patient_id,
            "user_id": patient_data.user_id,
            "registration_status": "success",
        }

    async def get_patient_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get patient profile by user ID."""
        patient = await self.db.patients.find_one({"user_id": user_id, "is_active": True})
        return patient

    async def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient profile by patient ID."""
        patient = await self.db.patients.find_one({"patient_id": patient_id, "is_active": True})
        return patient

    async def update_patient(self, user_id: str, update_data: PatientUpdate) -> Optional[Dict[str, Any]]:
        """Update patient profile."""
        update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items() if v is not None}
        if not update_dict:
            return await self.get_patient_by_user_id(user_id)

        update_dict["updated_at"] = datetime.utcnow()

        result = await self.db.patients.update_one(
            {"user_id": user_id, "is_active": True},
            {"$set": update_dict},
        )

        if result.matched_count == 0:
            raise ValueError("Patient not found")

        return await self.get_patient_by_user_id(user_id)

    async def add_medical_history(self, user_id: str, history_data: MedicalHistoryCreate) -> Dict[str, Any]:
        """Add medical history record for patient."""
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise ValueError("Patient not found")

        history_id = generate_id("MH")
        now = datetime.utcnow()
        history_doc = {
            "history_id": history_id,
            "patient_id": patient["patient_id"],
            "condition_name": history_data.condition_name,
            "diagnosis_date": history_data.diagnosis_date,
            "status": history_data.status.value,
            "treatment_notes": history_data.treatment_notes,
            "created_at": now,
            "updated_at": now,
        }

        await self.db.medical_history.insert_one(history_doc)

        return {
            "history_id": history_id,
            "patient_id": patient["patient_id"],
            "created_at": now,
        }

    async def get_medical_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all medical history for patient."""
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise ValueError("Patient not found")

        cursor = self.db.medical_history.find(
            {"patient_id": patient["patient_id"]},
            sort=[("diagnosis_date", -1)],
        )
        return await cursor.to_list(length=None)

    async def update_medical_history(
        self, user_id: str, history_id: str, update_data: MedicalHistoryUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update medical history record."""
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise ValueError("Patient not found")

        update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items() if v is not None}
        if not update_dict:
            return await self.get_medical_history_by_id(history_id)

        update_dict["updated_at"] = datetime.utcnow()

        result = await self.db.medical_history.update_one(
            {"history_id": history_id, "patient_id": patient["patient_id"]},
            {"$set": update_dict},
        )

        if result.matched_count == 0:
            raise ValueError("Medical history not found")

        return await self.get_medical_history_by_id(history_id)

    async def get_medical_history_by_id(self, history_id: str) -> Optional[Dict[str, Any]]:
        """Get medical history by ID."""
        return await self.db.medical_history.find_one({"history_id": history_id})

    async def add_allergy(self, user_id: str, allergy_data: AllergyCreate) -> Dict[str, Any]:
        """Add allergy record for patient."""
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise ValueError("Patient not found")

        allergy_id = generate_id("AL")
        now = datetime.utcnow()
        allergy_doc = {
            "allergy_id": allergy_id,
            "patient_id": patient["patient_id"],
            "allergy_name": allergy_data.allergy_name,
            "severity": allergy_data.severity.value,
            "reaction_description": allergy_data.reaction_description,
            "created_at": now,
        }

        await self.db.allergies.insert_one(allergy_doc)

        return {
            "allergy_id": allergy_id,
            "patient_id": patient["patient_id"],
            "created_at": now,
        }

    async def get_allergies(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all allergies for patient."""
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise ValueError("Patient not found")

        cursor = self.db.allergies.find(
            {"patient_id": patient["patient_id"]},
            sort=[("severity", -1)],
        )
        return await cursor.to_list(length=None)

    async def delete_allergy(self, user_id: str, allergy_id: str) -> Dict[str, str]:
        """Delete allergy record."""
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise ValueError("Patient not found")

        result = await self.db.allergies.delete_one({"allergy_id": allergy_id, "patient_id": patient["patient_id"]})

        if result.deleted_count == 0:
            raise ValueError("Allergy not found")

        return {
            "deletion_status": "success",
            "message": "Allergy record deleted successfully",
        }

    async def get_allergy_by_id(self, allergy_id: str) -> Optional[Dict[str, Any]]:
        """Get allergy by ID."""
        return await self.db.allergies.find_one({"allergy_id": allergy_id})

    async def add_insurance(self, user_id: str, insurance_data: InsuranceCreate) -> Dict[str, Any]:
        """Add or update insurance information."""
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise ValueError("Patient not found")

        # Check if insurance already exists and update
        existing = await self.db.insurance.find_one({"patient_id": patient["patient_id"]})
        if existing:
            update_dict = {
                "provider_name": insurance_data.provider_name,
                "policy_number": insurance_data.policy_number,
                "coverage_type": insurance_data.coverage_type.value,
                "expiry_date": insurance_data.expiry_date,
                "updated_at": datetime.utcnow(),
            }
            await self.db.insurance.update_one({"patient_id": patient["patient_id"]}, {"$set": update_dict})
            return {
                "insurance_id": existing["insurance_id"],
                "patient_id": patient["patient_id"],
                "created_at": existing["created_at"],
            }

        # Create new insurance record
        insurance_id = generate_id("IN")
        now = datetime.utcnow()
        insurance_doc = {
            "insurance_id": insurance_id,
            "patient_id": patient["patient_id"],
            "provider_name": insurance_data.provider_name,
            "policy_number": insurance_data.policy_number,
            "coverage_type": insurance_data.coverage_type.value,
            "expiry_date": insurance_data.expiry_date,
            "created_at": now,
            "updated_at": now,
        }

        await self.db.insurance.insert_one(insurance_doc)

        return {
            "insurance_id": insurance_id,
            "patient_id": patient["patient_id"],
            "created_at": now,
        }

    async def get_insurance(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get insurance information for patient."""
        patient = await self.get_patient_by_user_id(user_id)
        if not patient:
            raise ValueError("Patient not found")

        insurance = await self.db.insurance.find_one({"patient_id": patient["patient_id"]})
        return insurance

    async def get_insurance_by_id(self, insurance_id: str) -> Optional[Dict[str, Any]]:
        """Get insurance by ID."""
        return await self.db.insurance.find_one({"insurance_id": insurance_id})

    async def get_patient_count(self) -> int:
        """Get total count of active patients."""
        return await self.db.patients.count_documents({"is_active": True})
