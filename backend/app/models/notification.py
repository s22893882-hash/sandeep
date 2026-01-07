"""Notification-related data models."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Notification type levels."""

    appointment = "appointment"
    consultation = "consultation"
    payment = "payment"
    system = "system"


class NotificationChannel(str, Enum):
    """Notification channels."""

    email = "email"
    sms = "sms"
    push = "push"
    in_app = "in_app"


class Notification(BaseModel):
    """Notification model."""

    notification_id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any] = {}
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationPreference(BaseModel):
    """Notification preference model."""

    user_id: str
    channel_preferences: Dict[NotificationChannel, bool]
    opt_out_categories: List[NotificationType] = []


class PushToken(BaseModel):
    """Push token model."""

    user_id: str
    device_token: str
    device_type: str  # ios, android, web
    created_at: datetime = Field(default_factory=datetime.utcnow)
