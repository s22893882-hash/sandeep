"""Clinical notes service for managing consultation clinical notes."""
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import hashlib

from app.models.clinical_notes import (
    ClinicalNotesCreate,
    ClinicalNotesUpdate,
    ClinicalNotesResponse,
    Vitals,
)


class ClinicalNotesService:
    """Service for handling clinical notes management."""

    def __init__(self, db):
        """Initialize clinical notes service with database."""
        self.db = db

    async def generate_notes_id(self) -> str:
        """Generate a unique clinical notes ID."""
        return f"CN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:6]}"

    async def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive medical data.

        In production, this would use proper encryption (e.g., AES-256).
        For now, we'll use a simple hash for demonstration.

        Args:
            data: The data to encrypt

        Returns:
            Encrypted data
        """
        # Mock encryption - in production use proper encryption
        return hashlib.sha256(data.encode()).hexdigest()

    async def add_notes(
        self,
        consultation_id: str,
        doctor_id: str,
        notes_text: str,
        vitals: Optional[Dict[str, Any]] = None,
        diagnosis: Optional[str] = None,
        treatment_plan: Optional[str] = None,
    ) -> ClinicalNotesResponse:
        """
        Add clinical notes to a consultation.

        Args:
            consultation_id: The consultation ID
            doctor_id: The doctor user ID
            notes_text: The clinical notes
            vitals: Optional patient vitals
            diagnosis: Optional diagnosis
            treatment_plan: Optional treatment plan

        Returns:
            Created clinical notes response

        Raises:
            ValueError: If consultation not found or doctor not authorized
        """
        # Verify consultation exists
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if consultation["doctor_id"] != doctor_id:
            raise ValueError("Only the doctor can create clinical notes")

        # Encrypt sensitive data
        encrypted_notes = await self.encrypt_data(notes_text)

        notes_id = await self.generate_notes_id()
        created_at = datetime.utcnow()

        # Process vitals
        vitals_data = None
        if vitals:
            vitals_data = {
                "blood_pressure": vitals.get("blood_pressure"),
                "heart_rate": vitals.get("heart_rate"),
                "temperature": vitals.get("temperature"),
                "weight": vitals.get("weight"),
                "height": vitals.get("height"),
                "respiratory_rate": vitals.get("respiratory_rate"),
                "oxygen_saturation": vitals.get("oxygen_saturation"),
            }

        notes_data = {
            "notes_id": notes_id,
            "consultation_id": consultation_id,
            "doctor_id": doctor_id,
            "notes_text": encrypted_notes,  # Store encrypted
            "notes_text_plain": notes_text,  # Store plain text for testing (in production, only store encrypted)
            "vitals": vitals_data,
            "diagnosis": diagnosis,
            "treatment_plan": treatment_plan,
            "version": 1,
            "created_at": created_at,
            "updated_at": created_at,
        }

        await self.db.clinical_notes.insert_one(notes_data)

        # Convert vitals dict to Vitals model
        vitals_response = Vitals(**vitals_data) if vitals_data else None

        return ClinicalNotesResponse(
            notes_id=notes_id,
            consultation_id=consultation_id,
            doctor_id=doctor_id,
            notes_text=notes_text,
            vitals=vitals_response,
            diagnosis=diagnosis,
            treatment_plan=treatment_plan,
            version=1,
            created_at=created_at,
            updated_at=created_at,
        )

    async def get_notes(
        self, consultation_id: str, doctor_id: str
    ) -> ClinicalNotesResponse:
        """
        Get clinical notes for a consultation.

        Args:
            consultation_id: The consultation ID
            doctor_id: The doctor user ID

        Returns:
            Clinical notes response

        Raises:
            ValueError: If notes not found, doctor not authorized, or user is a patient
        """
        # Get notes
        notes = await self.db.clinical_notes.find_one(
            {"consultation_id": consultation_id}
        )

        if not notes:
            raise ValueError("Clinical notes not found")

        # Doctor-only access
        if notes["doctor_id"] != doctor_id:
            raise ValueError(
                "Only the treating doctor can view clinical notes"
            )

        # Convert vitals dict to Vitals model
        vitals_response = Vitals(**notes["vitals"]) if notes.get("vitals") else None

        # Return plain text for now (in production, would decrypt)
        notes_text = notes.get("notes_text_plain", notes["notes_text"])

        return ClinicalNotesResponse(
            notes_id=notes["notes_id"],
            consultation_id=notes["consultation_id"],
            doctor_id=notes["doctor_id"],
            notes_text=notes_text,
            vitals=vitals_response,
            diagnosis=notes.get("diagnosis"),
            treatment_plan=notes.get("treatment_plan"),
            version=notes.get("version", 1),
            created_at=notes["created_at"],
            updated_at=notes.get("updated_at"),
        )

    async def update_notes(
        self, notes_id: str, doctor_id: str, update_data: ClinicalNotesUpdate
    ) -> ClinicalNotesResponse:
        """
        Update clinical notes.

        Args:
            notes_id: The clinical notes ID
            doctor_id: The doctor user ID
            update_data: The update data

        Returns:
            Updated clinical notes response

        Raises:
            ValueError: If notes not found or doctor not authorized
        """
        # Get existing notes
        notes = await self.db.clinical_notes.find_one({"notes_id": notes_id})

        if not notes:
            raise ValueError("Clinical notes not found")

        if notes["doctor_id"] != doctor_id:
            raise ValueError("Only the treating doctor can update clinical notes")

        # Prepare update
        updated_at = datetime.utcnow()
        update_dict = {"updated_at": updated_at}

        if update_data.notes_text:
            update_dict["notes_text"] = await self.encrypt_data(update_data.notes_text)
            update_dict["notes_text_plain"] = update_data.notes_text

        if update_data.vitals:
            update_dict["vitals"] = {
                "blood_pressure": update_data.vitals.blood_pressure,
                "heart_rate": update_data.vitals.heart_rate,
                "temperature": update_data.vitals.temperature,
                "weight": update_data.vitals.weight,
                "height": update_data.vitals.height,
                "respiratory_rate": update_data.vitals.respiratory_rate,
                "oxygen_saturation": update_data.vitals.oxygen_saturation,
            }

        if update_data.diagnosis is not None:
            update_dict["diagnosis"] = update_data.diagnosis

        if update_data.treatment_plan is not None:
            update_dict["treatment_plan"] = update_data.treatment_plan

        # Increment version
        update_dict["version"] = notes.get("version", 1) + 1

        # Update notes
        updated_notes = await self.db.clinical_notes.find_one_and_update(
            {"notes_id": notes_id},
            {"$set": update_dict},
            return_document=True,
        )

        # Convert vitals dict to Vitals model
        vitals_response = Vitals(**updated_notes["vitals"]) if updated_notes.get("vitals") else None

        notes_text = updated_notes.get("notes_text_plain", updated_notes["notes_text"])

        return ClinicalNotesResponse(
            notes_id=updated_notes["notes_id"],
            consultation_id=updated_notes["consultation_id"],
            doctor_id=updated_notes["doctor_id"],
            notes_text=notes_text,
            vitals=vitals_response,
            diagnosis=updated_notes.get("diagnosis"),
            treatment_plan=updated_notes.get("treatment_plan"),
            version=updated_notes.get("version", 1),
            created_at=updated_notes["created_at"],
            updated_at=updated_notes["updated_at"],
        )
