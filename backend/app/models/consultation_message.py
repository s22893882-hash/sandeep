"""Consultation message-related data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Message type options."""

    text = "text"
    image = "image"
    file = "file"


class DeliveryStatus(str, Enum):
    """Message delivery status options."""

    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


class MessageCreate(BaseModel):
    """Message creation request model."""

    sender_id: str = Field(..., min_length=1)
    message_text: str = Field(..., min_length=1, max_length=5000)
    message_type: MessageType = MessageType.text


class MessageResponse(BaseModel):
    """Message response model."""

    message_id: str
    consultation_id: str
    sender_id: str
    sender_name: Optional[str] = None
    message_text: str
    message_type: str
    timestamp: datetime
    delivery_status: str
    is_read: bool = False
    read_at: Optional[datetime] = None


class MessagesListResponse(BaseModel):
    """Messages list response model."""

    messages: list[MessageResponse]
    total_count: int
    limit: int
    offset: int
