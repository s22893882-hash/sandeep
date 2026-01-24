"""Consultation service for managing consultation operations."""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.consultation import (
    ConsultationStatus,
    ConsultationResponse,
    ConsultationListResponse,
    ConsultationCloseResponse,
)


class ConsultationService:
    """Service for handling consultation business logic."""

    def __init__(self, db):
        """Initialize consultation service with database."""
        self.db = db

    async def generate_consultation_id(self) -> str:
        """Generate a unique consultation ID."""
        return f"CON{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:6]}"

    async def generate_session_token(self) -> str:
        """Generate a unique session token for messaging."""
        return uuid4().hex

    async def start_consultation(
        self, appointment_id: str, patient_id: str, doctor_id: str
    ) -> Dict[str, Any]:
        """
        Start a new consultation session.

        Args:
            appointment_id: The appointment ID
            patient_id: The patient user ID
            doctor_id: The doctor user ID

        Returns:
            Created consultation data

        Raises:
            ValueError: If appointment is invalid or already has an active consultation
        """
        # Check if appointment exists and is confirmed (simplified - in production would verify)
        consultation_id = await self.generate_consultation_id()
        session_token = await self.generate_session_token()
        start_time = datetime.utcnow()

        consultation_data = {
            "consultation_id": consultation_id,
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "status": ConsultationStatus.initiated.value,
            "start_time": start_time,
            "end_time": None,
            "duration_minutes": None,
            "session_token": session_token,
            "created_at": start_time,
            "updated_at": start_time,
        }

        await self.db.consultations.insert_one(consultation_data)

        return {
            "consultation_id": consultation_id,
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "status": ConsultationStatus.initiated.value,
            "session_token": session_token,
            "start_time": start_time.isoformat(),
            "created_at": start_time.isoformat(),
        }

    async def get_consultation(
        self, consultation_id: str, user_id: str, user_role: str
    ) -> Optional[ConsultationResponse]:
        """
        Get consultation details by ID.

        Args:
            consultation_id: The consultation ID
            user_id: The user ID requesting the consultation
            user_role: The role of the user (patient/doctor/admin)

        Returns:
            Consultation response data or None if not found

        Raises:
            ValueError: If user is not authorized to view this consultation
        """
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            return None

        # Authorization check
        if user_role != "admin":
            if user_id not in [
                consultation["patient_id"],
                consultation["doctor_id"],
            ]:
                raise ValueError("Not authorized to view this consultation")

        # Get counts
        messages_count = await self.db.consultation_messages.count_documents(
            {"consultation_id": consultation_id}
        )
        prescriptions_count = await self.db.prescriptions.count_documents(
            {"consultation_id": consultation_id}
        )
        documents_count = await self.db.consultation_documents.count_documents(
            {"consultation_id": consultation_id}
        )

        # Get participant names (simplified - in production would fetch from user/patient tables)
        patient_name = None
        doctor_name = None
        specialization = None

        return ConsultationResponse(
            consultation_id=consultation["consultation_id"],
            appointment_id=consultation["appointment_id"],
            patient_id=consultation["patient_id"],
            patient_name=patient_name,
            doctor_id=consultation["doctor_id"],
            doctor_name=doctor_name,
            specialization=specialization,
            status=consultation["status"],
            start_time=consultation.get("start_time"),
            end_time=consultation.get("end_time"),
            duration_minutes=consultation.get("duration_minutes"),
            session_token=consultation.get("session_token"),
            messages_count=messages_count,
            prescriptions_count=prescriptions_count,
            documents_count=documents_count,
            created_at=consultation["created_at"],
            updated_at=consultation.get("updated_at"),
        )

    async def close_consultation(
        self, consultation_id: str, doctor_id: str, end_notes: str
    ) -> ConsultationCloseResponse:
        """
        Close a consultation session.

        Args:
            consultation_id: The consultation ID
            doctor_id: The doctor user ID
            end_notes: Closing notes for the consultation

        Returns:
            Updated consultation close response

        Raises:
            ValueError: If consultation not found, not authorized, or already closed
        """
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if consultation["doctor_id"] != doctor_id:
            raise ValueError("Not authorized to close this consultation")

        if consultation["status"] == ConsultationStatus.completed.value:
            raise ValueError("Consultation is already closed")

        # Calculate duration
        start_time = consultation["start_time"]
        end_time = datetime.utcnow()
        duration = int((end_time - start_time).total_seconds() / 60)

        # Update consultation
        await self.db.consultations.update_one(
            {"consultation_id": consultation_id},
            {
                "$set": {
                    "status": ConsultationStatus.completed.value,
                    "end_time": end_time,
                    "duration_minutes": duration,
                    "updated_at": end_time,
                }
            },
        )

        return ConsultationCloseResponse(
            consultation_id=consultation_id,
            status=ConsultationStatus.completed.value,
            end_time=end_time,
            duration_minutes=duration,
            completion_summary="Consultation completed successfully",
        )

    async def update_status(
        self, consultation_id: str, doctor_id: str, new_status: ConsultationStatus
    ) -> Dict[str, Any]:
        """
        Update consultation status.

        Args:
            consultation_id: The consultation ID
            doctor_id: The doctor user ID
            new_status: The new status

        Returns:
            Updated consultation data

        Raises:
            ValueError: If consultation not found, not authorized, or invalid status transition
        """
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if consultation["doctor_id"] != doctor_id:
            raise ValueError("Not authorized to update this consultation")

        # Validate status transition
        current_status = consultation["status"]
        valid_transitions = {
            "initiated": ["in-progress", "cancelled"],
            "in-progress": ["completed", "cancelled"],
            "completed": [],
            "cancelled": [],
        }

        if new_status.value not in valid_transitions.get(current_status, []):
            raise ValueError(
                f"Invalid status transition from {current_status} to {new_status.value}"
            )

        # Update consultation
        await self.db.consultations.update_one(
            {"consultation_id": consultation_id},
            {
                "$set": {
                    "status": new_status.value,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        return {
            "consultation_id": consultation_id,
            "status": new_status.value,
            "status_change_timestamp": datetime.utcnow().isoformat(),
        }

    async def get_doctor_consultations(
        self, doctor_id: str, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get consultations for a doctor.

        Args:
            doctor_id: The doctor user ID
            filters: Filter criteria (date_range, patient_name, status)

        Returns:
            List of consultations for the doctor
        """
        query = {"doctor_id": doctor_id}

        # Apply filters
        if filters.get("status") and filters["status"] != "all":
            query["status"] = filters["status"]

        if filters.get("date_from") or filters.get("date_to"):
            date_filter = {}
            if filters.get("date_from"):
                date_filter["$gte"] = datetime.fromisoformat(filters["date_from"])
            if filters.get("date_to"):
                date_filter["$lte"] = datetime.fromisoformat(filters["date_to"])
            query["start_time"] = date_filter

        # Pagination
        limit = filters.get("limit", 10)
        offset = filters.get("offset", 0)

        cursor = self.db.consultations.find(query).sort("created_at", -1)
        total_count = await self.db.consultations.count_documents(query)
        cursor.skip(offset).limit(limit)

        consultations = []
        async for doc in cursor:
            # Check for prescriptions and clinical notes
            has_prescriptions = await self.db.prescriptions.count_documents(
                {"consultation_id": doc["consultation_id"]}
            ) > 0
            has_clinical_notes = await self.db.clinical_notes.count_documents(
                {"consultation_id": doc["consultation_id"]}
            ) > 0

            # Get feedback rating
            feedback = await self.db.consultation_feedback.find_one(
                {"consultation_id": doc["consultation_id"]}
            )
            feedback_rating = feedback.get("rating") if feedback else None

            consultations.append(
                ConsultationListResponse(
                    consultation_id=doc["consultation_id"],
                    doctor_id=doc["doctor_id"],
                    doctor_name=None,
                    specialization=None,
                    patient_id=doc["patient_id"],
                    patient_name=None,
                    status=doc["status"],
                    start_time=doc.get("start_time"),
                    end_time=doc.get("end_time"),
                    has_prescriptions=has_prescriptions,
                    has_clinical_notes=has_clinical_notes,
                    feedback_rating=feedback_rating,
                    created_at=doc["created_at"],
                )
            )

        return {
            "consultations": consultations,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    async def get_patient_consultations(
        self, patient_id: str, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get consultations for a patient.

        Args:
            patient_id: The patient user ID
            filters: Filter criteria (status, limit, offset)

        Returns:
            List of consultations for the patient
        """
        query = {"patient_id": patient_id}

        # Apply status filter
        if filters.get("status") and filters["status"] != "all":
            if filters["status"] == "pending-follow-up":
                # Check for scheduled follow-ups
                consultation_ids = []
                async for follow_up in self.db.follow_up_consultations.find(
                    {"status": "scheduled"}
                ):
                    consultation_ids.append(follow_up["original_consultation_id"])
                query["consultation_id"] = {"$in": consultation_ids}
            else:
                query["status"] = filters["status"]

        # Pagination
        limit = filters.get("limit", 10)
        offset = filters.get("offset", 0)

        cursor = self.db.consultations.find(query).sort("created_at", -1)
        total_count = await self.db.consultations.count_documents(query)
        cursor.skip(offset).limit(limit)

        consultations = []
        async for doc in cursor:
            # Get feedback rating
            feedback = await self.db.consultation_feedback.find_one(
                {"consultation_id": doc["consultation_id"]}
            )
            feedback_rating = feedback.get("rating") if feedback else None

            consultations.append(
                ConsultationListResponse(
                    consultation_id=doc["consultation_id"],
                    doctor_id=doc["doctor_id"],
                    doctor_name=None,
                    specialization=None,
                    patient_id=doc["patient_id"],
                    patient_name=None,
                    status=doc["status"],
                    start_time=doc.get("start_time"),
                    end_time=doc.get("end_time"),
                    has_prescriptions=False,
                    has_clinical_notes=False,
                    feedback_rating=feedback_rating,
                    created_at=doc["created_at"],
                )
            )

        return {
            "consultations": consultations,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }
