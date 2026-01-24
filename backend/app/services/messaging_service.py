"""Messaging service for handling consultation messages."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
from uuid import uuid4

from app.models.consultation_message import (
    MessageType,
    DeliveryStatus,
    MessageCreate,
    MessageResponse,
    MessagesListResponse,
)


class MessagingService:
    """Service for handling consultation messaging."""

    def __init__(self, db):
        """Initialize messaging service with database."""
        self.db = db

    async def generate_message_id(self) -> str:
        """Generate a unique message ID."""
        return f"MSG{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:6]}"

    async def send_message(
        self,
        consultation_id: str,
        sender_id: str,
        message_text: str,
        message_type: MessageType = MessageType.text,
    ) -> MessageResponse:
        """
        Send a message in a consultation.

        Args:
            consultation_id: The consultation ID
            sender_id: The sender user ID
            message_text: The message content
            message_type: The type of message

        Returns:
            Created message response

        Raises:
            ValueError: If consultation not found or sender is not a participant
        """
        # Verify consultation exists and sender is a participant
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if sender_id not in [
            consultation["patient_id"],
            consultation["doctor_id"],
        ]:
            raise ValueError("Only consultation participants can send messages")

        # Check if consultation is active
        if consultation["status"] in ["completed", "cancelled"]:
            raise ValueError("Cannot send messages to closed consultations")

        message_id = await self.generate_message_id()
        timestamp = datetime.utcnow()

        message_data = {
            "message_id": message_id,
            "consultation_id": consultation_id,
            "sender_id": sender_id,
            "message_text": message_text,
            "message_type": message_type.value,
            "timestamp": timestamp,
            "delivery_status": DeliveryStatus.delivered.value,
            "is_read": False,
            "read_at": None,
        }

        await self.db.consultation_messages.insert_one(message_data)

        # Get sender name (simplified - would fetch from user table in production)
        sender_name = None

        return MessageResponse(
            message_id=message_id,
            consultation_id=consultation_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message_text=message_text,
            message_type=message_type.value,
            timestamp=timestamp,
            delivery_status=DeliveryStatus.delivered.value,
            is_read=False,
            read_at=None,
        )

    async def get_messages(
        self,
        consultation_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        sort_order: str = "asc",
    ) -> MessagesListResponse:
        """
        Get messages for a consultation.

        Args:
            consultation_id: The consultation ID
            user_id: The user ID requesting the messages
            limit: Number of messages to return
            offset: Pagination offset
            sort_order: Sort order (asc = oldest first, desc = newest first)

        Returns:
            List of messages

        Raises:
            ValueError: If consultation not found or user is not authorized
        """
        # Verify consultation exists and user is a participant
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if user_id not in [
            consultation["patient_id"],
            consultation["doctor_id"],
        ]:
            raise ValueError("Not authorized to view these messages")

        # Get messages
        query = {"consultation_id": consultation_id}
        sort_direction = 1 if sort_order == "asc" else -1

        total_count = await self.db.consultation_messages.count_documents(query)
        cursor = (
            self.db.consultation_messages.find(query)
            .sort("timestamp", sort_direction)
            .skip(offset)
            .limit(limit)
        )

        messages = []
        async for doc in cursor:
            # Get sender name
            sender_name = None

            messages.append(
                MessageResponse(
                    message_id=doc["message_id"],
                    consultation_id=doc["consultation_id"],
                    sender_id=doc["sender_id"],
                    sender_name=sender_name,
                    message_text=doc["message_text"],
                    message_type=doc["message_type"],
                    timestamp=doc["timestamp"],
                    delivery_status=doc["delivery_status"],
                    is_read=doc.get("is_read", False),
                    read_at=doc.get("read_at"),
                )
            )

        return MessagesListResponse(
            messages=messages,
            total_count=total_count,
            limit=limit,
            offset=offset,
        )

    async def mark_as_read(
        self, consultation_id: str, user_id: str, message_ids: List[str]
    ) -> int:
        """
        Mark messages as read.

        Args:
            consultation_id: The consultation ID
            user_id: The user ID marking messages as read
            message_ids: List of message IDs to mark as read

        Returns:
            Number of messages marked as read

        Raises:
            ValueError: If user is not authorized
        """
        # Verify consultation exists and user is a participant
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if user_id not in [
            consultation["patient_id"],
            consultation["doctor_id"],
        ]:
            raise ValueError("Not authorized to mark these messages as read")

        # Only mark messages sent by the other participant
        other_participant_id = (
            consultation["doctor_id"]
            if user_id == consultation["patient_id"]
            else consultation["patient_id"]
        )

        read_at = datetime.utcnow()

        result = await self.db.consultation_messages.update_many(
            {
                "consultation_id": consultation_id,
                "sender_id": other_participant_id,
                "message_id": {"$in": message_ids},
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": read_at,
                    "delivery_status": DeliveryStatus.read.value,
                }
            },
        )

        return result.modified_count

    async def search_messages(
        self, consultation_id: str, user_id: str, search_query: str
    ) -> List[MessageResponse]:
        """
        Search messages in a consultation.

        Args:
            consultation_id: The consultation ID
            user_id: The user ID searching
            search_query: The search query

        Returns:
            List of matching messages

        Raises:
            ValueError: If user is not authorized
        """
        # Verify consultation exists and user is a participant
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if user_id not in [
            consultation["patient_id"],
            consultation["doctor_id"],
        ]:
            raise ValueError("Not authorized to search these messages")

        # Search messages
        query = {
            "consultation_id": consultation_id,
            "message_text": {"$regex": search_query, "$options": "i"},
        }

        cursor = self.db.consultation_messages.find(query).sort("timestamp", -1)

        messages = []
        async for doc in cursor:
            sender_name = None

            messages.append(
                MessageResponse(
                    message_id=doc["message_id"],
                    consultation_id=doc["consultation_id"],
                    sender_id=doc["sender_id"],
                    sender_name=sender_name,
                    message_text=doc["message_text"],
                    message_type=doc["message_type"],
                    timestamp=doc["timestamp"],
                    delivery_status=doc["delivery_status"],
                    is_read=doc.get("is_read", False),
                    read_at=doc.get("read_at"),
                )
            )

        return messages
