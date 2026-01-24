"""Feedback service for managing consultation feedback."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from app.models.consultation_feedback import (
    FeedbackCreate,
    FeedbackResponse,
)


class FeedbackService:
    """Service for handling feedback management."""

    def __init__(self, db):
        """Initialize feedback service with database."""
        self.db = db

    async def generate_feedback_id(self) -> str:
        """Generate a unique feedback ID."""
        return f"FB{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:6]}"

    async def submit_feedback(
        self,
        consultation_id: str,
        patient_id: str,
        rating: int,
        feedback_text: str = None,
        would_recommend: bool = None,
        anonymous: bool = False,
    ) -> FeedbackResponse:
        """
        Submit feedback for a consultation.

        Args:
            consultation_id: The consultation ID
            patient_id: The patient user ID
            rating: The rating (1-5)
            feedback_text: Optional feedback text
            would_recommend: Optional recommendation flag
            anonymous: Whether feedback is anonymous

        Returns:
            Created feedback response

        Raises:
            ValueError: If consultation not found or patient not authorized
        """
        # Verify consultation exists
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if consultation["patient_id"] != patient_id:
            raise ValueError("Only the patient can submit feedback")

        # Check if consultation is completed
        if consultation["status"] != "completed":
            raise ValueError("Feedback can only be submitted for completed consultations")

        # Check if feedback already exists
        existing_feedback = await self.db.consultation_feedback.find_one(
            {"consultation_id": consultation_id}
        )
        if existing_feedback:
            raise ValueError("Feedback has already been submitted for this consultation")

        # Validate rating
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        feedback_id = await self.generate_feedback_id()
        created_at = datetime.utcnow()

        feedback_data = {
            "feedback_id": feedback_id,
            "consultation_id": consultation_id,
            "patient_id": patient_id,
            "rating": rating,
            "feedback_text": feedback_text,
            "would_recommend": would_recommend,
            "anonymous": anonymous,
            "created_at": created_at,
        }

        await self.db.consultation_feedback.insert_one(feedback_data)

        # Get patient name (unless anonymous)
        patient_name = None
        if not anonymous:
            # In production, would fetch from user table
            patient_name = "Patient"

        return FeedbackResponse(
            feedback_id=feedback_id,
            consultation_id=consultation_id,
            rating=rating,
            feedback_text=feedback_text,
            would_recommend=would_recommend,
            patient_name=patient_name,
            created_at=created_at,
        )

    async def get_feedback(self, consultation_id: str) -> FeedbackResponse:
        """
        Get feedback for a consultation.

        Args:
            consultation_id: The consultation ID

        Returns:
            Feedback response

        Raises:
            ValueError: If feedback not found
        """
        feedback = await self.db.consultation_feedback.find_one(
            {"consultation_id": consultation_id}
        )

        if not feedback:
            raise ValueError("Feedback not found")

        # Get patient name (unless anonymous)
        patient_name = None
        if not feedback.get("anonymous"):
            # In production, would fetch from user table
            patient_name = "Patient"

        return FeedbackResponse(
            feedback_id=feedback["feedback_id"],
            consultation_id=feedback["consultation_id"],
            rating=feedback["rating"],
            feedback_text=feedback.get("feedback_text"),
            would_recommend=feedback.get("would_recommend"),
            patient_name=patient_name,
            created_at=feedback["created_at"],
        )

    async def get_doctor_rating(self, doctor_id: str) -> Dict[str, Any]:
        """
        Get overall rating for a doctor.

        Args:
            doctor_id: The doctor user ID

        Returns:
            Doctor rating statistics
        """
        # Get all consultations for doctor
        consultations_cursor = self.db.consultations.find(
            {"doctor_id": doctor_id}
        )

        consultation_ids = []
        async for consultation in consultations_cursor:
            consultation_ids.append(consultation["consultation_id"])

        # Get feedback for these consultations
        feedback_cursor = self.db.consultation_feedback.find(
            {"consultation_id": {"$in": consultation_ids}}
        )

        ratings = []
        would_recommend_count = 0
        total_count = 0

        async for feedback in feedback_cursor:
            ratings.append(feedback["rating"])
            if feedback.get("would_recommend"):
                would_recommend_count += 1
            total_count += 1

        if not ratings:
            return {
                "doctor_id": doctor_id,
                "average_rating": None,
                "total_reviews": 0,
                "recommendation_rate": None,
            }

        average_rating = sum(ratings) / len(ratings)
        recommendation_rate = (would_recommend_count / total_count) * 100 if total_count > 0 else 0

        return {
            "doctor_id": doctor_id,
            "average_rating": round(average_rating, 2),
            "total_reviews": total_count,
            "recommendation_rate": round(recommendation_rate, 2),
        }
