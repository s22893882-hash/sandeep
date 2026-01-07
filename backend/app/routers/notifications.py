"""Notification management API endpoints."""
from fastapi import APIRouter, Depends
from typing import Optional, Dict, Any

from app.auth import get_current_user
from app.services.notification_service import NotificationService
from app.database import get_database

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def get_notification_service(db=Depends(get_database)) -> NotificationService:
    """Get notification service instance."""
    return NotificationService(db)


@router.post("/send", response_model=dict)
async def send_notification(
    user_id: str,
    n_type: str,
    title: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Send notification."""
    return await service.send_notification(user_id, n_type, title, message, data)


@router.get("/preferences", response_model=dict)
async def get_preferences(
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get notification preferences."""
    return await service.get_preferences(current_user["user_id"])


@router.put("/preferences", response_model=dict)
async def update_preferences(
    prefs_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Update preferences."""
    return await service.update_preferences(current_user["user_id"], prefs_data)


@router.get("/inbox", response_model=list)
async def get_inbox(
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get notification inbox."""
    return await service.get_inbox(current_user["user_id"])


@router.put("/{id}/read", response_model=dict)
async def mark_read(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark as read."""
    return await service.mark_as_read(id)


@router.delete("/{id}", response_model=dict)
async def delete_notification(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Delete notification."""
    return await service.delete_notification(id)


@router.post("/subscribe", response_model=dict)
async def subscribe(
    token: str,
    device_type: str,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Subscribe to push notifications."""
    return await service.subscribe_push(current_user["user_id"], token, device_type)


@router.post("/test", response_model=dict)
async def test_notification(
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Test notification delivery."""
    return await service.test_notification(current_user["user_id"])
