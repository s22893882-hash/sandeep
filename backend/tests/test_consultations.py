"""Tests for consultation management endpoints."""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.consultation import (
    ConsultationStatus,
    ConsultationCreate,
    ConsultationUpdate,
    ConsultationResponse,
    ConsultationListResponse,
    ConsultationCloseRequest,
    StatusUpdateRequest,
)
from app.services.consultation_service import ConsultationService


@pytest.fixture
def mock_consultation():
    """Create a mock consultation."""
    return {
        "_id": ObjectId(),
        "consultation_id": "CON20240117120000001",
        "appointment_id": "APT123",
        "patient_id": "patient123",
        "doctor_id": "doctor123",
        "status": "initiated",
        "start_time": datetime.utcnow(),
        "end_time": None,
        "duration_minutes": None,
        "session_token": "session_token_abc123",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def consultation_service(db):
    """Create consultation service instance."""
    return ConsultationService(db)


# Unit Tests for ConsultationService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_consultation_success(consultation_service, db):
    """Test starting a new consultation successfully."""
    # Insert mock appointment (simplified - would verify in production)
    result = await consultation_service.start_consultation(
        "APT123", "patient123", "doctor123"
    )

    assert "consultation_id" in result
    assert result["appointment_id"] == "APT123"
    assert result["patient_id"] == "patient123"
    assert result["doctor_id"] == "doctor123"
    assert result["status"] == "initiated"
    assert "session_token" in result
    assert "start_time" in result

    # Verify consultation was stored
    consultation = await db.consultations.find_one(
        {"consultation_id": result["consultation_id"]}
    )
    assert consultation is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_consultation_success(consultation_service, db, mock_consultation):
    """Test getting consultation details successfully."""
    await db.consultations.insert_one(mock_consultation)

    consultation = await consultation_service.get_consultation(
        mock_consultation["consultation_id"],
        mock_consultation["patient_id"],
        "patient",
    )

    assert consultation is not None
    assert consultation.consultation_id == mock_consultation["consultation_id"]
    assert consultation.patient_id == mock_consultation["patient_id"]
    assert consultation.doctor_id == mock_consultation["doctor_id"]
    assert consultation.status == mock_consultation["status"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_consultation_not_found(consultation_service):
    """Test getting non-existent consultation."""
    consultation = await consultation_service.get_consultation(
        "NONEXISTENT", "user123", "patient"
    )
    assert consultation is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_consultation_unauthorized(consultation_service, db, mock_consultation):
    """Test getting consultation without authorization."""
    await db.consultations.insert_one(mock_consultation)

    with pytest.raises(ValueError, match="Not authorized"):
        await consultation_service.get_consultation(
            mock_consultation["consultation_id"],
            "unauthorized_user",
            "patient",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_consultation_success(consultation_service, db, mock_consultation):
    """Test closing a consultation successfully."""
    await db.consultations.insert_one(mock_consultation)

    result = await consultation_service.close_consultation(
        mock_consultation["consultation_id"],
        mock_consultation["doctor_id"],
        "Patient advised to follow treatment plan",
    )

    assert result.status == "completed"
    assert result.duration_minutes >= 0
    assert "end_time" in result

    # Verify consultation was updated
    consultation = await db.consultations.find_one(
        {"consultation_id": mock_consultation["consultation_id"]}
    )
    assert consultation["status"] == "completed"
    assert consultation["end_time"] is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_consultation_not_found(consultation_service):
    """Test closing non-existent consultation."""
    with pytest.raises(ValueError, match="Consultation not found"):
        await consultation_service.close_consultation(
            "NONEXISTENT", "doctor123", "End notes"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_consultation_unauthorized(consultation_service, db, mock_consultation):
    """Test closing consultation without authorization."""
    await db.consultations.insert_one(mock_consultation)

    with pytest.raises(ValueError, match="Not authorized"):
        await consultation_service.close_consultation(
            mock_consultation["consultation_id"],
            "unauthorized_doctor",
            "End notes",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_status_success(consultation_service, db, mock_consultation):
    """Test updating consultation status successfully."""
    await db.consultations.insert_one(mock_consultation)

    result = await consultation_service.update_status(
        mock_consultation["consultation_id"],
        mock_consultation["doctor_id"],
        ConsultationStatus.in_progress,
    )

    assert result["status"] == "in-progress"
    assert "status_change_timestamp" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_status_invalid_transition(consultation_service, db):
    """Test updating status with invalid transition."""
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

    with pytest.raises(ValueError, match="Invalid status transition"):
        await consultation_service.update_status(
            mock_consultation["consultation_id"],
            mock_consultation["doctor_id"],
            ConsultationStatus.in_progress,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_doctor_consultations(consultation_service, db, mock_consultation):
    """Test getting doctor's consultations."""
    await db.consultations.insert_one(mock_consultation)

    result = await consultation_service.get_doctor_consultations(
        mock_consultation["doctor_id"], {"limit": 10, "offset": 0}
    )

    assert "consultations" in result
    assert result["total_count"] >= 1
    assert len(result["consultations"]) >= 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_patient_consultations(consultation_service, db, mock_consultation):
    """Test getting patient's consultations."""
    await db.consultations.insert_one(mock_consultation)

    result = await consultation_service.get_patient_consultations(
        mock_consultation["patient_id"], {"limit": 10, "offset": 0}
    )

    assert "consultations" in result
    assert result["total_count"] >= 1
    assert len(result["consultations"]) >= 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_patient_consultations_with_status_filter(
    consultation_service, db, mock_consultation
):
    """Test getting patient's consultations with status filter."""
    await db.consultations.insert_one(mock_consultation)

    result = await consultation_service.get_patient_consultations(
        mock_consultation["patient_id"],
        {"status": "initiated", "limit": 10, "offset": 0},
    )

    assert "consultations" in result
    all(
        c.status == "initiated" for c in result["consultations"]
    )


# Endpoint Tests


@pytest.mark.integration
@pytest.mark.asyncio
async def test_start_consultation_endpoint(client, auth_headers):
    """Test starting consultation via API endpoint."""
    response = await client.post(
        "/api/consultations/start",
        json={
            "appointment_id": "APT123",
            "patient_id": "patient123",
            "doctor_id": "doctor123",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert "consultation_id" in data
    assert data["status"] == "initiated"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_consultation_endpoint(client, db, auth_headers, mock_consultation):
    """Test getting consultation via API endpoint."""
    await db.consultations.insert_one(mock_consultation)

    response = await client.get(
        f"/api/consultations/{mock_consultation['consultation_id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["consultation_id"] == mock_consultation["consultation_id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_close_consultation_endpoint(client, db, auth_headers, mock_consultation):
    """Test closing consultation via API endpoint."""
    await db.consultations.insert_one(mock_consultation)

    response = await client.put(
        f"/api/consultations/{mock_consultation['consultation_id']}/close",
        json={"end_notes": "Patient advised to rest"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_status_endpoint(client, db, auth_headers, mock_consultation):
    """Test updating consultation status via API endpoint."""
    await db.consultations.insert_one(mock_consultation)

    response = await client.put(
        f"/api/consultations/{mock_consultation['consultation_id']}/status",
        json={"status": "in-progress"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in-progress"
