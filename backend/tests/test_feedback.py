"""Tests for feedback management."""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from bson import ObjectId
from typing import Dict

from app.models.consultation_feedback import (
    FeedbackCreate,
    FeedbackResponse,
)
from app.services.feedback_service import FeedbackService


@pytest.fixture
def mock_consultation_completed():
    """Create a mock completed consultation."""
    return {
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


@pytest.fixture
def mock_consultation_active():
    """Create a mock active consultation."""
    return {
        "_id": ObjectId(),
        "consultation_id": "CON124",
        "appointment_id": "APT124",
        "patient_id": "patient123",
        "doctor_id": "doctor123",
        "status": "in-progress",
        "start_time": datetime.utcnow(),
        "end_time": None,
        "duration_minutes": None,
        "session_token": "token124",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_feedback():
    """Create a mock feedback."""
    return {
        "_id": ObjectId(),
        "feedback_id": "FB123",
        "consultation_id": "CON123",
        "patient_id": "patient123",
        "rating": 5,
        "feedback_text": "Excellent consultation",
        "would_recommend": True,
        "anonymous": False,
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def feedback_service(db):
    """Create feedback service instance."""
    return FeedbackService(db)


# Unit Tests for FeedbackService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_feedback_success(feedback_service, db, mock_consultation_completed):
    """Test submitting feedback successfully."""
    await db.consultations.insert_one(mock_consultation_completed)

    feedback = await feedback_service.submit_feedback(
        consultation_id="CON123",
        patient_id="patient123",
        rating=5,
        feedback_text="Excellent consultation",
        would_recommend=True,
        anonymous=False,
    )

    assert feedback.consultation_id == "CON123"
    assert feedback.rating == 5
    assert feedback.feedback_text == "Excellent consultation"
    assert feedback.would_recommend is True
    assert feedback.anonymous is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_feedback_anonymous(feedback_service, db, mock_consultation_completed):
    """Test submitting anonymous feedback."""
    await db.consultations.insert_one(mock_consultation_completed)

    feedback = await feedback_service.submit_feedback(
        consultation_id="CON123",
        patient_id="patient123",
        rating=4,
        anonymous=True,
    )

    assert feedback.anonymous is True
    assert feedback.patient_name is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_feedback_unauthorized(feedback_service, db, mock_consultation_completed):
    """Test submitting feedback without authorization."""
    await db.consultations.insert_one(mock_consultation_completed)

    with pytest.raises(ValueError, match="Only the patient can submit feedback"):
        await feedback_service.submit_feedback(
            consultation_id="CON123",
            patient_id="unauthorized_patient",
            rating=5,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_feedback_active_consultation(feedback_service, db, mock_consultation_active):
    """Test submitting feedback for active consultation."""
    await db.consultations.insert_one(mock_consultation_active)

    with pytest.raises(ValueError, match="Feedback can only be submitted for completed consultations"):
        await feedback_service.submit_feedback(
            consultation_id="CON124",
            patient_id="patient123",
            rating=5,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_feedback_already_exists(feedback_service, db, mock_consultation_completed, mock_feedback):
    """Test submitting feedback when it already exists."""
    await db.consultations.insert_one(mock_consultation_completed)
    await db.consultation_feedback.insert_one(mock_feedback)

    with pytest.raises(ValueError, match="Feedback has already been submitted"):
        await feedback_service.submit_feedback(
            consultation_id="CON123",
            patient_id="patient123",
            rating=5,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_feedback_invalid_rating_low(feedback_service, db, mock_consultation_completed):
    """Test submitting feedback with invalid rating (too low)."""
    await db.consultations.insert_one(mock_consultation_completed)

    with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
        await feedback_service.submit_feedback(
            consultation_id="CON123",
            patient_id="patient123",
            rating=0,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_feedback_invalid_rating_high(feedback_service, db, mock_consultation_completed):
    """Test submitting feedback with invalid rating (too high)."""
    await db.consultations.insert_one(mock_consultation_completed)

    with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
        await feedback_service.submit_feedback(
            consultation_id="CON123",
            patient_id="patient123",
            rating=6,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_feedback(feedback_service, db, mock_feedback):
    """Test getting feedback successfully."""
    await db.consultation_feedback.insert_one(mock_feedback)

    feedback = await feedback_service.get_feedback("CON123")

    assert feedback.feedback_id == "FB123"
    assert feedback.consultation_id == "CON123"
    assert feedback.rating == 5
    assert feedback.feedback_text == "Excellent consultation"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_feedback_not_found(feedback_service):
    """Test getting non-existent feedback."""
    with pytest.raises(ValueError, match="Feedback not found"):
        await feedback_service.get_feedback("NONEXISTENT")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_doctor_rating(feedback_service, db, mock_consultation_completed, mock_feedback):
    """Test getting doctor's overall rating."""
    await db.consultations.insert_one(mock_consultation_completed)
    await db.consultation_feedback.insert_one(mock_feedback)

    rating = await feedback_service.get_doctor_rating("doctor123")

    assert rating["doctor_id"] == "doctor123"
    assert rating["average_rating"] == 5.0
    assert rating["total_reviews"] == 1
    assert rating["recommendation_rate"] == 100.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_doctor_rating_multiple(feedback_service, db, mock_consultation_completed):
    """Test getting doctor's rating with multiple feedback entries."""
    await db.consultations.insert_one(mock_consultation_completed)

    # Add multiple feedback entries
    await db.consultation_feedback.insert_many([
        {
            "_id": ObjectId(),
            "feedback_id": "FB1",
            "consultation_id": "CON123",
            "patient_id": "patient1",
            "rating": 5,
            "feedback_text": "Great",
            "would_recommend": True,
            "anonymous": False,
            "created_at": datetime.utcnow(),
        },
        {
            "_id": ObjectId(),
            "feedback_id": "FB2",
            "consultation_id": "CON124",
            "patient_id": "patient2",
            "rating": 4,
            "feedback_text": "Good",
            "would_recommend": True,
            "anonymous": False,
            "created_at": datetime.utcnow(),
        },
        {
            "_id": ObjectId(),
            "feedback_id": "FB3",
            "consultation_id": "CON125",
            "patient_id": "patient3",
            "rating": 3,
            "feedback_text": "Okay",
            "would_recommend": False,
            "anonymous": False,
            "created_at": datetime.utcnow(),
        },
    ])

    rating = await feedback_service.get_doctor_rating("doctor123")

    assert rating["total_reviews"] == 3
    assert rating["average_rating"] == 4.0
    assert rating["recommendation_rate"] == 66.67


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_doctor_rating_no_feedback(feedback_service, db, mock_consultation_completed):
    """Test getting doctor's rating when no feedback exists."""
    await db.consultations.insert_one(mock_consultation_completed)

    rating = await feedback_service.get_doctor_rating("doctor123")

    assert rating["total_reviews"] == 0
    assert rating["average_rating"] is None
    assert rating["recommendation_rate"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_feedback_id(feedback_service):
    """Test generating unique feedback ID."""
    id1 = await feedback_service.generate_feedback_id()
    id2 = await feedback_service.generate_feedback_id()

    assert id1 != id2
    assert id1.startswith("FB")


# Endpoint Tests


@pytest.mark.integration
@pytest.mark.asyncio
async def test_submit_feedback_endpoint(client, db, auth_headers, mock_consultation_completed):
    """Test submitting feedback via API endpoint."""
    await db.consultations.insert_one(mock_consultation_completed)

    response = await client.post(
        "/api/consultations/CON123/feedback",
        json={
            "rating": 5,
            "feedback_text": "Excellent consultation",
            "would_recommend": True,
            "anonymous": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["consultation_id"] == "CON123"
    assert data["rating"] == 5
    assert data["feedback_text"] == "Excellent consultation"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_feedback_endpoint(client, db, auth_headers, mock_feedback):
    """Test getting feedback via API endpoint."""
    await db.consultation_feedback.insert_one(mock_feedback)

    response = await client.get(
        "/api/consultations/CON123/feedback",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["feedback_id"] == "FB123"
    assert data["rating"] == 5
