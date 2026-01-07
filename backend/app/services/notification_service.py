"""Notification management business logic."""
from typing import List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import generate_id


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def send_notification(
        self, user_id: str, n_type: str, title: str, message: str, data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send notification."""
        notification_id = generate_id("NOT")
        notification_doc = {
            "notification_id": notification_id,
            "user_id": user_id,
            "type": n_type,
            "title": title,
            "message": message,
            "data": data or {},
            "read": False,
            "created_at": datetime.utcnow(),
        }
        await self.db.notifications.insert_one(notification_doc)

        # Here we would also trigger email/SMS/Push via external services

        return notification_doc

    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get notification preferences."""
        prefs = await self.db.notification_preferences.find_one({"user_id": user_id})
        if not prefs:
            # Default preferences
            return {
                "user_id": user_id,
                "channel_preferences": {"email": True, "sms": False, "push": True, "in_app": True},
                "opt_out_categories": [],
            }
        return prefs

    async def update_preferences(self, user_id: str, prefs_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update preferences."""
        await self.db.notification_preferences.update_one({"user_id": user_id}, {"$set": prefs_data}, upsert=True)
        return await self.get_preferences(user_id)

    async def get_inbox(self, user_id: str) -> List[Dict[str, Any]]:
        """Get notification inbox."""
        cursor = self.db.notifications.find({"user_id": user_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def mark_as_read(self, notification_id: str) -> Dict[str, Any]:
        """Mark as read."""
        await self.db.notifications.update_one({"notification_id": notification_id}, {"$set": {"read": True}})
        return {"notification_id": notification_id, "read": True}

    async def delete_notification(self, notification_id: str) -> Dict[str, Any]:
        """Delete notification."""
        await self.db.notifications.delete_one({"notification_id": notification_id})
        return {"notification_id": notification_id, "deleted": True}

    async def subscribe_push(self, user_id: str, token: str, device_type: str) -> Dict[str, Any]:
        """Subscribe to push notifications."""
        doc = {"user_id": user_id, "device_token": token, "device_type": device_type, "created_at": datetime.utcnow()}
        await self.db.push_tokens.update_one({"user_id": user_id, "device_token": token}, {"$set": doc}, upsert=True)
        return {"status": "subscribed"}

    async def test_notification(self, user_id: str) -> Dict[str, Any]:
        """Test notification delivery."""
        return await self.send_notification(
            user_id, "system", "Test Notification", "This is a test notification from the Federated Health AI Platform."
        )
