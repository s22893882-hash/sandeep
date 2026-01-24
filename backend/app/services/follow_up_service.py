"""Follow-up service for managing follow-up consultations."""
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4

from app.models.follow_up_consultation import (
    FollowUpCreate,
    FollowUpResponse,
    FollowUpPriority,
    FollowUpStatus,
)


class FollowUpService:
    """Service for handling follow-up consultation management."""

    def __init__(self, db):
        """Initialize follow-up service with database."""
        self.db = db

    async def generate_follow_up_id(self) -> str:
        """Generate a unique follow-up consultation ID."""
        return f"FU{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:6]}"

    async def schedule_follow_up(
        self,
        original_consultation_id: str,
        doctor_id: str,
        follow_up_date: str,
        follow_up_time: str,
        reason: str,
        priority: FollowUpPriority = FollowUpPriority.medium,
    ) -> FollowUpResponse:
        """
        Schedule a follow-up consultation.

        Args:
            original_consultation_id: The original consultation ID
            doctor_id: The doctor user ID
            follow_up_date: The follow-up date (ISO format)
            follow_up_time: The follow-up time (HH:MM format)
            reason: The reason for follow-up
            priority: The priority level

        Returns:
            Created follow-up response

        Raises:
            ValueError: If original consultation not found or doctor not authorized
        """
        # Verify original consultation exists
        consultation = await self.db.consultations.find_one(
            {"consultation_id": original_consultation_id}
        )

        if not consultation:
            raise ValueError("Original consultation not found")

        if consultation["doctor_id"] != doctor_id:
            raise ValueError("Only the doctor can schedule follow-ups")

        follow_up_id = await self.generate_follow_up_id()
        created_at = datetime.utcnow()

        follow_up_data = {
            "follow_up_consultation_id": follow_up_id,
            "original_consultation_id": original_consultation_id,
            "doctor_id": doctor_id,
            "patient_id": consultation["patient_id"],
            "scheduled_date": follow_up_date,
            "scheduled_time": follow_up_time,
            "reason": reason,
            "priority": priority.value,
            "status": FollowUpStatus.scheduled.value,
            "created_at": created_at,
        }

        await self.db.follow_up_consultations.insert_one(follow_up_data)

        # Auto-notify patient (mock notification)
        # In production, would send email/push notification

        return FollowUpResponse(
            follow_up_consultation_id=follow_up_id,
            original_consultation_id=original_consultation_id,
            scheduled_date=follow_up_date,
            scheduled_time=follow_up_time,
            reason=reason,
            priority=priority.value,
            status=FollowUpStatus.scheduled.value,
            created_at=created_at,
        )

    async def get_follow_ups(self, consultation_id: str) -> List[FollowUpResponse]:
        """
        Get follow-up consultations for an original consultation.

        Args:
            consultation_id: The original consultation ID

        Returns:
            List of follow-up consultations
        """
        cursor = self.db.follow_up_consultations.find(
            {"original_consultation_id": consultation_id}
        ).sort("scheduled_date", -1)

        follow_ups = []
        async for doc in cursor:
            follow_ups.append(
                FollowUpResponse(
                    follow_up_consultation_id=doc["follow_up_consultation_id"],
                    original_consultation_id=doc["original_consultation_id"],
                    scheduled_date=doc["scheduled_date"],
                    scheduled_time=doc["scheduled_time"],
                    reason=doc["reason"],
                    priority=doc["priority"],
                    status=doc["status"],
                    created_at=doc["created_at"],
                )
            )

        return follow_ups

    async def get_patient_follow_ups(self, patient_id: str) -> List[FollowUpResponse]:
        """
        Get follow-up consultations for a patient.

        Args:
            patient_id: The patient user ID

        Returns:
            List of follow-up consultations
        """
        cursor = self.db.follow_up_consultations.find(
            {"patient_id": patient_id}
        ).sort("scheduled_date", -1)

        follow_ups = []
        async for doc in cursor:
            follow_ups.append(
                FollowUpResponse(
                    follow_up_consultation_id=doc["follow_up_consultation_id"],
                    original_consultation_id=doc["original_consultation_id"],
                    scheduled_date=doc["scheduled_date"],
                    scheduled_time=doc["scheduled_time"],
                    reason=doc["reason"],
                    priority=doc["priority"],
                    status=doc["status"],
                    created_at=doc["created_at"],
                )
            )

        return follow_ups

    async def get_doctor_follow_ups(self, doctor_id: str) -> List[FollowUpResponse]:
        """
        Get follow-up consultations for a doctor.

        Args:
            doctor_id: The doctor user ID

        Returns:
            List of follow-up consultations
        """
        cursor = self.db.follow_up_consultations.find(
            {"doctor_id": doctor_id}
        ).sort("scheduled_date", -1)

        follow_ups = []
        async for doc in cursor:
            follow_ups.append(
                FollowUpResponse(
                    follow_up_consultation_id=doc["follow_up_consultation_id"],
                    original_consultation_id=doc["original_consultation_id"],
                    scheduled_date=doc["scheduled_date"],
                    scheduled_time=doc["scheduled_time"],
                    reason=doc["reason"],
                    priority=doc["priority"],
                    status=doc["status"],
                    created_at=doc["created_at"],
                )
            )

        return follow_ups
