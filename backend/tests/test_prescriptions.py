"""Tests for prescription management."""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.prescription import (
    PrescriptionStatus,
    PrescriptionCreate,
    PrescriptionResponse,
    Medication,
)
from app.services.prescription_service import PrescriptionService


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
def mock_prescription():
    """Create a mock prescription."""
    return {
        "_id": ObjectId(),
        "prescription_id": "RX123",
        "consultation_id": "CON123",
        "doctor_id": "doctor123",
        "patient_id": "patient123",
        "medications": [
            {
                "medication_name": "Aspirin",
                "dosage": "500mg",
                "frequency": "Twice daily",
                "duration": "7 days",
                "instructions": "Take with food",
            }
        ],
        "notes": "For pain relief",
        "qr_code": "base64_encoded_qr",
        "prescription_status": "active",
        "issued_date": datetime.utcnow(),
        "expiry_date": datetime.utcnow() + timedelta(days=90),
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def prescription_service(db):
    """Create prescription service instance."""
    return PrescriptionService(db)


# Unit Tests for PrescriptionService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_prescription_success(prescription_service, db, mock_consultation):
    """Test adding a prescription successfully."""
    await db.consultations.insert_one(mock_consultation)

    medications = [
        Medication(
            medication_name="Aspirin",
            dosage="500mg",
            frequency="Twice daily",
            duration="7 days",
            instructions="Take with food",
        )
    ]

    prescription = await prescription_service.add_prescription(
        "CON123", "doctor123", medications, "For pain relief"
    )

    assert prescription.consultation_id == "CON123"
    assert prescription.doctor_id == "doctor123"
    assert len(prescription.medications) == 1
    assert prescription.medications[0].medication_name == "Aspirin"
    assert prescription.prescription_status == "active"
    assert prescription.qr_code is not None
    assert prescription.is_expired is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_prescription_unauthorized(prescription_service, db, mock_consultation):
    """Test adding prescription without authorization."""
    await db.consultations.insert_one(mock_consultation)

    medications = [Medication(
        medication_name="Aspirin",
        dosage="500mg",
        frequency="Twice daily",
        duration="7 days",
        instructions="Take with food",
    )]

    with pytest.raises(ValueError, match="Only the doctor can create prescriptions"):
        await prescription_service.add_prescription(
            "CON123", "unauthorized_doctor", medications
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_prescription_consultation_not_found(prescription_service):
    """Test adding prescription to non-existent consultation."""
    medications = [Medication(
        medication_name="Aspirin",
        dosage="500mg",
        frequency="Twice daily",
        duration="7 days",
        instructions="Take with food",
    )]

    with pytest.raises(ValueError, match="Consultation not found"):
        await prescription_service.add_prescription(
            "NONEXISTENT", "doctor123", medications
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_prescription_multiple_medications(prescription_service, db, mock_consultation):
    """Test adding prescription with multiple medications."""
    await db.consultations.insert_one(mock_consultation)

    medications = [
        Medication(
            medication_name="Aspirin",
            dosage="500mg",
            frequency="Twice daily",
            duration="7 days",
            instructions="Take with food",
        ),
        Medication(
            medication_name="Ibuprofen",
            dosage="200mg",
            frequency="Three times daily",
            duration="5 days",
            instructions="Take after meals",
        ),
    ]

    prescription = await prescription_service.add_prescription(
        "CON123", "doctor123", medications
    )

    assert len(prescription.medications) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_prescriptions(prescription_service, db, mock_consultation, mock_prescription):
    """Test getting prescriptions for a consultation."""
    await db.consultations.insert_one(mock_consultation)
    await db.prescriptions.insert_one(mock_prescription)

    prescriptions = await prescription_service.get_prescriptions("CON123")

    assert len(prescriptions) >= 1
    assert prescriptions[0].consultation_id == "CON123"
    assert len(prescriptions[0].medications) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_prescriptions_empty(prescription_service, db, mock_consultation):
    """Test getting prescriptions when none exist."""
    await db.consultations.insert_one(mock_consultation)

    prescriptions = await prescription_service.get_prescriptions("CON123")

    assert len(prescriptions) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_expiry_active(prescription_service, db, mock_prescription):
    """Test checking expiry for active prescription."""
    await db.prescriptions.insert_one(mock_prescription)

    is_expired = await prescription_service.check_expiry("RX123")

    assert is_expired is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_expiry_expired(prescription_service, db):
    """Test checking expiry for expired prescription."""
    expired_prescription = {
        "_id": ObjectId(),
        "prescription_id": "RX123",
        "consultation_id": "CON123",
        "doctor_id": "doctor123",
        "patient_id": "patient123",
        "medications": [],
        "notes": None,
        "qr_code": "base64_qr",
        "prescription_status": "active",
        "issued_date": datetime.utcnow() - timedelta(days=100),
        "expiry_date": datetime.utcnow() - timedelta(days=10),
        "created_at": datetime.utcnow() - timedelta(days=100),
    }
    await db.prescriptions.insert_one(expired_prescription)

    is_expired = await prescription_service.check_expiry("RX123")

    assert is_expired is True

    # Verify status was updated
    prescription = await db.prescriptions.find_one({"prescription_id": "RX123"})
    assert prescription["prescription_status"] == "expired"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_expiry_not_found(prescription_service):
    """Test checking expiry for non-existent prescription."""
    with pytest.raises(ValueError, match="Prescription not found"):
        await prescription_service.check_expiry("NONEXISTENT")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_qr_code(prescription_service):
    """Test QR code generation."""
    qr_code = await prescription_service.generate_qr_code("RX123")

    assert qr_code is not None
    assert qr_code.startswith("data:image/png;base64,")


# Endpoint Tests


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_prescription_endpoint(client, db, auth_headers, mock_consultation):
    """Test adding prescription via API endpoint."""
    await db.consultations.insert_one(mock_consultation)

    response = await client.post(
        "/api/consultations/CON123/prescription",
        json={
            "medications": [
                {
                    "medication_name": "Aspirin",
                    "dosage": "500mg",
                    "frequency": "Twice daily",
                    "duration": "7 days",
                    "instructions": "Take with food",
                }
            ],
            "notes": "For pain relief",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["consultation_id"] == "CON123"
    assert data["prescription_status"] == "active"
    assert "qr_code" in data
    assert len(data["medications"]) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_prescriptions_endpoint(client, db, auth_headers, mock_consultation, mock_prescription):
    """Test getting prescriptions via API endpoint."""
    await db.consultations.insert_one(mock_consultation)
    await db.prescriptions.insert_one(mock_prescription)

    response = await client.get(
        "/api/consultations/CON123/prescriptions",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "prescriptions" in data
    assert data["total_count"] >= 1
    assert len(data["prescriptions"]) >= 1
