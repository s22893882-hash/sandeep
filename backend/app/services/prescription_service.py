"""Prescription service for managing consultation prescriptions."""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from uuid import uuid4
import base64

from app.models.prescription import (
    PrescriptionStatus,
    PrescriptionCreate,
    PrescriptionResponse,
    Prescription as PrescriptionModel,
)


class PrescriptionService:
    """Service for handling prescription management."""

    def __init__(self, db):
        """Initialize prescription service with database."""
        self.db = db

    async def generate_prescription_id(self) -> str:
        """Generate a unique prescription ID."""
        return f"RX{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:6]}"

    async def generate_qr_code(self, prescription_id: str) -> str:
        """
        Generate a QR code for the prescription.

        In production, this would use a QR code library like qrcode.
        For now, we'll generate a mock base64 QR code.

        Args:
            prescription_id: The prescription ID

        Returns:
            Base64 encoded QR code
        """
        # Mock QR code generation
        qr_data = f"PRESCRIPTION:{prescription_id}"
        qr_base64 = base64.b64encode(qr_data.encode()).decode()
        return f"data:image/png;base64,{qr_base64}"

    async def add_prescription(
        self,
        consultation_id: str,
        doctor_id: str,
        medications: List[PrescriptionModel],
        notes: str = None,
    ) -> PrescriptionResponse:
        """
        Add a prescription to a consultation.

        Args:
            consultation_id: The consultation ID
            doctor_id: The doctor user ID
            medications: List of medications
            notes: Optional notes

        Returns:
            Created prescription response

        Raises:
            ValueError: If consultation not found or doctor not authorized
        """
        # Verify consultation exists and get patient_id
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if consultation["doctor_id"] != doctor_id:
            raise ValueError("Only the doctor can create prescriptions")

        prescription_id = await self.generate_prescription_id()
        issued_date = datetime.utcnow()
        expiry_date = issued_date + timedelta(days=90)  # 3 months default
        qr_code = await self.generate_qr_code(prescription_id)

        # Convert medications to dicts
        medications_list = [
            {
                "medication_name": med.medication_name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "duration": med.duration,
                "instructions": med.instructions,
            }
            for med in medications
        ]

        prescription_data = {
            "prescription_id": prescription_id,
            "consultation_id": consultation_id,
            "doctor_id": doctor_id,
            "patient_id": consultation["patient_id"],
            "medications": medications_list,
            "notes": notes,
            "qr_code": qr_code,
            "prescription_status": PrescriptionStatus.active.value,
            "issued_date": issued_date,
            "expiry_date": expiry_date,
            "created_at": issued_date,
        }

        await self.db.prescriptions.insert_one(prescription_data)

        # Convert medications back to model
        medications_response = [PrescriptionModel(**med) for med in medications_list]

        return PrescriptionResponse(
            prescription_id=prescription_id,
            consultation_id=consultation_id,
            doctor_id=doctor_id,
            patient_id=consultation["patient_id"],
            medications=medications_response,
            notes=notes,
            qr_code=qr_code,
            prescription_status=PrescriptionStatus.active.value,
            issued_date=issued_date,
            expiry_date=expiry_date,
            is_expired=False,
            created_at=issued_date,
        )

    async def get_prescriptions(self, consultation_id: str) -> List[PrescriptionResponse]:
        """
        Get all prescriptions for a consultation.

        Args:
            consultation_id: The consultation ID

        Returns:
            List of prescriptions
        """
        cursor = self.db.prescriptions.find(
            {"consultation_id": consultation_id}
        ).sort("issued_date", -1)

        prescriptions = []
        async for doc in cursor:
            medications_list = [
                PrescriptionModel(**med) for med in doc["medications"]
            ]
            is_expired = doc["expiry_date"] < datetime.utcnow()

            prescriptions.append(
                PrescriptionResponse(
                    prescription_id=doc["prescription_id"],
                    consultation_id=doc["consultation_id"],
                    doctor_id=doc["doctor_id"],
                    patient_id=doc["patient_id"],
                    medications=medications_list,
                    notes=doc.get("notes"),
                    qr_code=doc["qr_code"],
                    prescription_status=doc["prescription_status"],
                    issued_date=doc["issued_date"],
                    expiry_date=doc["expiry_date"],
                    is_expired=is_expired,
                    created_at=doc["created_at"],
                )
            )

        return prescriptions

    async def check_expiry(self, prescription_id: str) -> bool:
        """
        Check if a prescription is expired.

        Args:
            prescription_id: The prescription ID

        Returns:
            True if expired, False otherwise

        Raises:
            ValueError: If prescription not found
        """
        prescription = await self.db.prescriptions.find_one(
            {"prescription_id": prescription_id}
        )

        if not prescription:
            raise ValueError("Prescription not found")

        is_expired = prescription["expiry_date"] < datetime.utcnow()

        # Update status if expired
        if is_expired and prescription["prescription_status"] == PrescriptionStatus.active.value:
            await self.db.prescriptions.update_one(
                {"prescription_id": prescription_id},
                {"$set": {"prescription_status": PrescriptionStatus.expired.value}}
            )

        return is_expired
