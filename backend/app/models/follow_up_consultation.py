"""Follow-up consultation-related data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FollowUpPriority(str):
    """Follow-up priority options."""

    low = "low"
    medium = "medium"
    high = "high"


class FollowUpStatus(str):
    """Follow-up status options."""

    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class FollowUpCreate(BaseModel):
    """Follow-up creation request model."""

    follow_up_date: str = Field(..., min_length=1)
    follow_up_time: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1, max_length=1000)
    priority: FollowUpPriority = FollowUpPriority.medium


class FollowUpResponse(BaseModel):
    """Follow-up response model."""

    follow_up_consultation_id: str
    original_consultation_id: str
    scheduled_date: str
    scheduled_time: str
    reason: str
    priority: str
    status: str
    created_at: datetime
