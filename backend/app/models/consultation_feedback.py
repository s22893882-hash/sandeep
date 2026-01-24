"""Consultation feedback-related data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FeedbackCreate(BaseModel):
    """Feedback creation request model."""

    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = Field(None, max_length=2000)
    would_recommend: Optional[bool] = None
    anonymous: bool = False


class FeedbackResponse(BaseModel):
    """Feedback response model."""

    feedback_id: str
    consultation_id: str
    rating: int
    feedback_text: Optional[str] = None
    would_recommend: Optional[bool] = None
    patient_name: Optional[str] = None
    created_at: datetime
