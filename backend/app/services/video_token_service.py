"""Video token service for generating video call tokens."""
from typing import Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.follow_up_consultation import FollowUpPriority


class VideoTokenService:
    """Service for handling video token generation."""

    def __init__(self, db):
        """Initialize video token service with database."""
        self.db = db

    async def generate_token(
        self,
        consultation_id: str,
        participant_id: str,
        participant_type: str,
        session_duration: int = 60,
    ) -> Dict[str, Any]:
        """
        Generate a video call token.

        In production, this would integrate with Agora, Twilio, or similar services.
        For now, we'll generate a mock token.

        Args:
            consultation_id: The consultation ID
            participant_id: The participant user ID
            participant_type: The participant type (doctor/patient)
            session_duration: Session duration in minutes

        Returns:
            Video token response

        Raises:
            ValueError: If consultation not found or participant not authorized
        """
        # Verify consultation exists
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        # Verify participant is authorized
        if participant_type == "doctor":
            if consultation["doctor_id"] != participant_id:
                raise ValueError("Not authorized to generate video token")
        elif participant_type == "patient":
            if consultation["patient_id"] != participant_id:
                raise ValueError("Not authorized to generate video token")
        else:
            raise ValueError("Invalid participant type")

        # Generate mock token
        video_token = f"token_{uuid4().hex}"
        channel_name = f"consultation_{consultation_id}"
        rtc_uid = f"{participant_type}_{participant_id[:8]}"

        # Calculate token expiry
        token_expiry = datetime.utcnow() + timedelta(minutes=session_duration)

        # In production, would call Agora/Twilio API
        # For example:
        # from agora import Agora
        # agora = Agora(app_id, app_certificate)
        # video_token = agora.generate_token(channel_name, rtc_uid, role, expiry)

        return {
            "video_token": video_token,
            "channel_name": channel_name,
            "rtc_uid": rtc_uid,
            "token_expiry": token_expiry.isoformat(),
            "video_service": "agora",  # Would be the actual service in production
        }

    async def validate_token(self, token: str) -> bool:
        """
        Validate a video token.

        Args:
            token: The video token to validate

        Returns:
            True if valid, False otherwise
        """
        # Mock validation - in production would validate with video service
        # For now, check if token format is correct
        if not token or not token.startswith("token_"):
            return False

        return True
