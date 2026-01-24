"""Tests for consultation messaging endpoints."""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from bson import ObjectId

from app.models.consultation_message import (
    MessageType,
    DeliveryStatus,
    MessageCreate,
    MessageResponse,
)
from app.services.messaging_service import MessagingService


@pytest.fixture
def mock_consultation():
    """Create a mock consultation."""
    return {
        "_id": ObjectId(),
        "consultation_id": "CON123",
        "appointment_id": "APT123",
        "patient_id": "patient123",
        "doctor_id": "doctor123",
        "status": "in-progress",
        "start_time": datetime.utcnow(),
        "end_time": None,
        "duration_minutes": None,
        "session_token": "token123",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_message():
    """Create a mock message."""
    return {
        "_id": ObjectId(),
        "message_id": "MSG123",
        "consultation_id": "CON123",
        "sender_id": "doctor123",
        "message_text": "Hello patient",
        "message_type": "text",
        "timestamp": datetime.utcnow(),
        "delivery_status": "delivered",
        "is_read": False,
        "read_at": None,
    }


@pytest.fixture
def messaging_service(db):
    """Create messaging service instance."""
    return MessagingService(db)


# Unit Tests for MessagingService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_message_success(messaging_service, db, mock_consultation):
    """Test sending a message successfully."""
    await db.consultations.insert_one(mock_consultation)

    message = await messaging_service.send_message(
        "CON123", "doctor123", "Hello patient", MessageType.text
    )

    assert message.consultation_id == "CON123"
    assert message.sender_id == "doctor123"
    assert message.message_text == "Hello patient"
    assert message.message_type == "text"
    assert message.delivery_status == "delivered"
    assert message.is_read is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_message_consultation_not_found(messaging_service):
    """Test sending message to non-existent consultation."""
    with pytest.raises(ValueError, match="Consultation not found"):
        await messaging_service.send_message(
            "NONEXISTENT", "doctor123", "Hello", MessageType.text
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_message_unauthorized(messaging_service, db, mock_consultation):
    """Test sending message without authorization."""
    await db.consultations.insert_one(mock_consultation)

    with pytest.raises(ValueError, match="Only consultation participants"):
        await messaging_service.send_message(
            "CON123", "unauthorized_user", "Hello", MessageType.text
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_message_to_closed_consultation(messaging_service, db):
    """Test sending message to closed consultation."""
    mock_consultation = {
        "_id": ObjectId(),
        "consultation_id": "CON123",
        "appointment_id": "APT123",
        "patient_id": "patient123",
        "doctor_id": "doctor123",
        "status": "completed",
        "start_time": datetime.utcnow(),
        "end_time": datetime.utcnow(),
        "duration_minutes": 30,
        "session_token": "token123",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await db.consultations.insert_one(mock_consultation)

    with pytest.raises(ValueError, match="Cannot send messages to closed consultations"):
        await messaging_service.send_message(
            "CON123", "doctor123", "Hello", MessageType.text
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_messages_success(messaging_service, db, mock_consultation, mock_message):
    """Test getting messages successfully."""
    await db.consultations.insert_one(mock_consultation)
    await db.consultation_messages.insert_one(mock_message)

    messages = await messaging_service.get_messages(
        "CON123", "doctor123", 50, 0, "asc"
    )

    assert len(messages.messages) >= 1
    assert messages.total_count >= 1
    assert messages.limit == 50
    assert messages.offset == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_messages_unauthorized(messaging_service, db, mock_consultation):
    """Test getting messages without authorization."""
    await db.consultations.insert_one(mock_consultation)

    with pytest.raises(ValueError, match="Not authorized"):
        await messaging_service.get_messages(
            "CON123", "unauthorized_user", 50, 0, "asc"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mark_as_read_success(messaging_service, db, mock_consultation, mock_message):
    """Test marking messages as read successfully."""
    await db.consultations.insert_one(mock_consultation)
    await db.consultation_messages.insert_one(mock_message)

    count = await messaging_service.mark_as_read(
        "CON123", "patient123", ["MSG123"]
    )

    assert count == 1

    # Verify message was marked as read
    message = await db.consultation_messages.find_one({"message_id": "MSG123"})
    assert message["is_read"] is True
    assert message["read_at"] is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_messages_success(messaging_service, db, mock_consultation, mock_message):
    """Test searching messages successfully."""
    await db.consultations.insert_one(mock_consultation)
    await db.consultation_messages.insert_one(mock_message)

    messages = await messaging_service.search_messages("CON123", "doctor123", "Hello")

    assert len(messages) >= 1
    assert all("Hello" in m.message_text for m in messages)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_messages_unauthorized(messaging_service, db, mock_consultation):
    """Test searching messages without authorization."""
    await db.consultations.insert_one(mock_consultation)

    with pytest.raises(ValueError, match="Not authorized"):
        await messaging_service.search_messages("CON123", "unauthorized_user", "Hello")


# Endpoint Tests


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_message_endpoint(client, db, auth_headers, mock_consultation):
    """Test sending message via API endpoint."""
    await db.consultations.insert_one(mock_consultation)

    response = await client.post(
        "/api/consultations/CON123/message",
        json={
            "sender_id": "doctor123",
            "message_text": "Hello patient",
            "message_type": "text",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["consultation_id"] == "CON123"
    assert data["message_text"] == "Hello patient"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_messages_endpoint(client, db, auth_headers, mock_consultation, mock_message):
    """Test getting messages via API endpoint."""
    await db.consultations.insert_one(mock_consultation)
    await db.consultation_messages.insert_one(mock_message)

    response = await client.get(
        "/api/consultations/CON123/messages?limit=50&offset=0&sort_order=asc",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert data["total_count"] >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_messages_pagination(client, db, auth_headers, mock_consultation):
    """Test message pagination."""
    await db.consultations.insert_one(mock_consultation)

    # Insert multiple messages
    for i in range(10):
        await db.consultation_messages.insert_one({
            "message_id": f"MSG{i}",
            "consultation_id": "CON123",
            "sender_id": "doctor123",
            "message_text": f"Message {i}",
            "message_type": "text",
            "timestamp": datetime.utcnow(),
            "delivery_status": "delivered",
            "is_read": False,
            "read_at": None,
        })

    response = await client.get(
        "/api/consultations/CON123/messages?limit=5&offset=0",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 5
    assert data["limit"] == 5
    assert data["offset"] == 0
