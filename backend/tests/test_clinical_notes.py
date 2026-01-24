"""Tests for clinical notes management."""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from bson import ObjectId

from app.models.clinical_notes import (
    ClinicalNotesCreate,
    ClinicalNotesUpdate,
    ClinicalNotesResponse,
    Vitals,
)
from app.services.clinical_notes_service import ClinicalNotesService


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
def mock_clinical_notes():
    """Create a mock clinical notes."""
    return {
        "_id": ObjectId(),
        "notes_id": "CN123",
        "consultation_id": "CON123",
        "doctor_id": "doctor123",
        "notes_text": "encrypted_notes_hash",
        "notes_text_plain": "Patient presents with chest pain",
        "vitals": {
            "blood_pressure": "120/80",
            "heart_rate": 72,
            "temperature": 98.6,
            "weight": 70,
            "height": 175,
            "respiratory_rate": 16,
            "oxygen_saturation": 98,
        },
        "diagnosis": "Musculoskeletal chest pain",
        "treatment_plan": "Rest and pain management",
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def clinical_notes_service(db):
    """Create clinical notes service instance."""
    return ClinicalNotesService(db)


# Unit Tests for ClinicalNotesService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_notes_success(clinical_notes_service, db, mock_consultation):
    """Test adding clinical notes successfully."""
    await db.consultations.insert_one(mock_consultation)

    vitals = Vitals(
        blood_pressure="120/80",
        heart_rate=72,
        temperature=98.6,
        weight=70,
    )

    notes = await clinical_notes_service.add_notes(
        consultation_id="CON123",
        doctor_id="doctor123",
        notes_text="Patient presents with chest pain",
        vitals=vitals.dict(),
        diagnosis="Musculoskeletal chest pain",
        treatment_plan="Rest and pain management",
    )

    assert notes.consultation_id == "CON123"
    assert notes.doctor_id == "doctor123"
    assert notes.notes_text == "Patient presents with chest pain"
    assert notes.diagnosis == "Musculoskeletal chest pain"
    assert notes.treatment_plan == "Rest and pain management"
    assert notes.vitals.blood_pressure == "120/80"
    assert notes.vitals.heart_rate == 72
    assert notes.version == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_notes_unauthorized(clinical_notes_service, db, mock_consultation):
    """Test adding notes without authorization."""
    await db.consultations.insert_one(mock_consultation)

    with pytest.raises(ValueError, match="Only the doctor can create clinical notes"):
        await clinical_notes_service.add_notes(
            consultation_id="CON123",
            doctor_id="unauthorized_doctor",
            notes_text="Test notes",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_notes_consultation_not_found(clinical_notes_service):
    """Test adding notes to non-existent consultation."""
    with pytest.raises(ValueError, match="Consultation not found"):
        await clinical_notes_service.add_notes(
            consultation_id="NONEXISTENT",
            doctor_id="doctor123",
            notes_text="Test notes",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_notes_success(clinical_notes_service, db, mock_clinical_notes):
    """Test getting clinical notes successfully."""
    await db.clinical_notes.insert_one(mock_clinical_notes)

    notes = await clinical_notes_service.get_notes("CON123", "doctor123")

    assert notes.notes_id == "CN123"
    assert notes.consultation_id == "CON123"
    assert notes.notes_text == "Patient presents with chest pain"
    assert notes.diagnosis == "Musculoskeletal chest pain"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_notes_doctor_only(clinical_notes_service, db, mock_clinical_notes):
    """Test that only doctor can access clinical notes."""
    await db.clinical_notes.insert_one(mock_clinical_notes)

    with pytest.raises(ValueError, match="Only the treating doctor"):
        await clinical_notes_service.get_notes("CON123", "other_doctor123")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_notes_not_found(clinical_notes_service):
    """Test getting non-existent clinical notes."""
    with pytest.raises(ValueError, match="Clinical notes not found"):
        await clinical_notes_service.get_notes("NONEXISTENT", "doctor123")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_notes_success(clinical_notes_service, db, mock_clinical_notes):
    """Test updating clinical notes successfully."""
    await db.clinical_notes.insert_one(mock_clinical_notes)

    vitals = Vitals(
        blood_pressure="125/85",
        heart_rate=75,
        temperature=98.8,
    )

    update_data = ClinicalNotesUpdate(
        notes_text="Updated notes text",
        vitals=vitals,
        diagnosis="Updated diagnosis",
    )

    updated_notes = await clinical_notes_service.update_notes(
        "CN123", "doctor123", update_data
    )

    assert updated_notes.notes_text == "Updated notes text"
    assert updated_notes.diagnosis == "Updated diagnosis"
    assert updated_notes.vitals.blood_pressure == "125/85"
    assert updated_notes.version == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_notes_unauthorized(clinical_notes_service, db, mock_clinical_notes):
    """Test updating notes without authorization."""
    await db.clinical_notes.insert_one(mock_clinical_notes)

    update_data = ClinicalNotesUpdate(notes_text="Updated notes")

    with pytest.raises(ValueError, match="Only the treating doctor"):
        await clinical_notes_service.update_notes("CN123", "unauthorized_doctor", update_data)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_encrypt_data(clinical_notes_service):
    """Test data encryption."""
    data = "Sensitive patient information"
    encrypted = await clinical_notes_service.encrypt_data(data)

    assert encrypted is not None
    assert encrypted != data
    assert len(encrypted) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_notes_without_vitals(clinical_notes_service, db, mock_consultation):
    """Test adding clinical notes without vitals."""
    await db.consultations.insert_one(mock_consultation)

    notes = await clinical_notes_service.add_notes(
        consultation_id="CON123",
        doctor_id="doctor123",
        notes_text="Patient is stable",
    )

    assert notes.vitals is None
    assert notes.notes_text == "Patient is stable"


# Endpoint Tests


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_clinical_notes_endpoint(client, db, auth_headers, mock_consultation):
    """Test adding clinical notes via API endpoint."""
    await db.consultations.insert_one(mock_consultation)

    response = await client.post(
        "/api/consultations/CON123/notes",
        json={
            "notes_text": "Patient presents with chest pain",
            "vitals": {
                "blood_pressure": "120/80",
                "heart_rate": 72,
                "temperature": 98.6,
                "weight": 70,
            },
            "diagnosis": "Musculoskeletal chest pain",
            "treatment_plan": "Rest and pain management",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["consultation_id"] == "CON123"
    assert data["notes_text"] == "Patient presents with chest pain"
    assert data["diagnosis"] == "Musculoskeletal chest pain"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_clinical_notes_endpoint(client, db, auth_headers, mock_clinical_notes):
    """Test getting clinical notes via API endpoint."""
    await db.clinical_notes.insert_one(mock_clinical_notes)

    response = await client.get(
        "/api/consultations/CON123/notes",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes_id"] == "CN123"
    assert data["notes_text"] == "Patient presents with chest pain"
