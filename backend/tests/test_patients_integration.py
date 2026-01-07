"""Integration tests for patient management API endpoints."""
import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

os.environ["ENVIRONMENT"] = "test"


@pytest.fixture
def mock_database():
    """Mock MongoDB database for testing."""
    db = Mock()
    db.patients = Mock()
    db.medical_history = Mock()
    db.allergies = Mock()
    db.insurance = Mock()
    db.create_index = AsyncMock()
    db.create_indexes = AsyncMock()
    return db


@pytest.fixture
def mock_patient_data():
    """Mock patient data."""
    return {
        "_id": "507f1f77bcf86cd799439011",
        "patient_id": "PT20240101120000001",
        "user_id": "user123",
        "full_name": "John Doe",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "blood_type": "O+",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "emergency_contact_name": "Jane Doe",
        "emergency_contact_phone": "1234567890",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
    }


@pytest.fixture
def mock_medical_history_data():
    """Mock medical history data."""
    return {
        "_id": "507f1f77bcf86cd799439012",
        "history_id": "MH20240101120000001",
        "patient_id": "PT20240101120000001",
        "condition_name": "Diabetes Type 2",
        "diagnosis_date": "2020-01-01",
        "status": "active",
        "treatment_notes": "Metformin 500mg twice daily",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_allergy_data():
    """Mock allergy data."""
    return {
        "_id": "507f1f77bcf86cd799439013",
        "allergy_id": "AL20240101120000001",
        "patient_id": "PT20240101120000001",
        "allergy_name": "Penicillin",
        "severity": "severe",
        "reaction_description": "Anaphylactic reaction",
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_insurance_data():
    """Mock insurance data."""
    return {
        "_id": "507f1f77bcf86cd799439014",
        "insurance_id": "IN20240101120000001",
        "patient_id": "PT20240101120000001",
        "provider_name": "BlueCross BlueShield",
        "policy_number": "BCB123456789",
        "coverage_type": "premium",
        "expiry_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


# Integration tests for all 12 endpoints


@pytest.mark.integration
async def test_register_patient_endpoint(mock_database, mock_patient_data):
    """Test POST /api/patients/register endpoint."""
    from app.services.patient_service import PatientService
    from app.models.patient import PatientCreate

    mock_database.patients.find_one = AsyncMock(return_value=None)
    mock_database.patients.insert_one = AsyncMock()

    service = PatientService(mock_database)
    patient_data = PatientCreate(
        user_id="user123",
        date_of_birth="1990-01-01",
        gender="male",
        blood_type="O+",
        height_cm=175.0,
        weight_kg=70.0,
        emergency_contact_name="Jane Doe",
        emergency_contact_phone="1234567890",
    )

    result = await service.register_patient(patient_data)

    assert result["registration_status"] == "success"
    assert "patient_id" in result
    mock_database.patients.insert_one.assert_called_once()


@pytest.mark.integration
async def test_get_patient_profile_endpoint(mock_database, mock_patient_data):
    """Test GET /api/patients/profile endpoint."""
    from app.services.patient_service import PatientService

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)

    service = PatientService(mock_database)
    result = await service.get_patient_by_user_id("user123")

    assert result is not None
    assert result["patient_id"] == "PT20240101120000001"
    assert result["user_id"] == "user123"


@pytest.mark.integration
async def test_update_patient_profile_endpoint(mock_database, mock_patient_data):
    """Test PUT /api/patients/profile endpoint."""
    from app.services.patient_service import PatientService
    from app.models.patient import PatientUpdate

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.patients.update_one = AsyncMock(return_value=Mock(matched_count=1))

    service = PatientService(mock_database)
    update_data = PatientUpdate(height_cm=180.0, weight_kg=75.0)

    result = await service.update_patient("user123", update_data)

    assert result is not None
    mock_database.patients.update_one.assert_called_once()


@pytest.mark.integration
async def test_add_medical_history_endpoint(mock_database, mock_patient_data):
    """Test POST /api/patients/medical-history endpoint."""
    from app.services.patient_service import PatientService
    from app.models.patient import MedicalHistoryCreate

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.medical_history.insert_one = AsyncMock()

    service = PatientService(mock_database)
    history_data = MedicalHistoryCreate(
        condition_name="Hypertension",
        diagnosis_date="2021-01-01",
        status="active",
        treatment_notes="ACE inhibitors",
    )

    result = await service.add_medical_history("user123", history_data)

    assert "history_id" in result
    mock_database.medical_history.insert_one.assert_called_once()


@pytest.mark.integration
async def test_get_medical_history_endpoint(mock_database, mock_patient_data):
    """Test GET /api/patients/medical-history endpoint."""
    from app.services.patient_service import PatientService

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(
        return_value=[
            {
                "history_id": "MH1",
                "patient_id": "PT123",
                "condition_name": "Diabetes",
                "diagnosis_date": "2020-01-01",
                "status": "active",
                "treatment_notes": "Insulin therapy",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        ]
    )
    mock_database.medical_history.find = Mock(return_value=mock_cursor)

    service = PatientService(mock_database)
    result = await service.get_medical_history("user123")

    assert len(result) == 1
    assert result[0]["condition_name"] == "Diabetes"


@pytest.mark.integration
async def test_update_medical_history_endpoint(mock_database, mock_patient_data):
    """Test PUT /api/patients/medical-history/{history_id} endpoint."""
    from app.services.patient_service import PatientService
    from app.models.patient import MedicalHistoryUpdate

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.medical_history.update_one = AsyncMock(return_value=Mock(matched_count=1))
    mock_database.medical_history.find_one = AsyncMock(
        return_value={
            "history_id": "MH1",
            "status": "resolved",
            "treatment_notes": "Updated notes",
            "patient_id": "PT123",
            "condition_name": "Diabetes",
            "diagnosis_date": "2020-01-01",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )

    service = PatientService(mock_database)
    update_data = MedicalHistoryUpdate(status="resolved", treatment_notes="Updated notes")

    result = await service.update_medical_history("user123", "MH1", update_data)

    assert result is not None
    assert result["status"] == "resolved"
    mock_database.medical_history.update_one.assert_called_once()


@pytest.mark.integration
async def test_add_allergy_endpoint(mock_database, mock_patient_data):
    """Test POST /api/patients/allergies endpoint."""
    from app.services.patient_service import PatientService
    from app.models.patient import AllergyCreate

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.allergies.insert_one = AsyncMock()

    service = PatientService(mock_database)
    allergy_data = AllergyCreate(allergy_name="Peanuts", severity="severe", reaction_description="Anaphylaxis")

    result = await service.add_allergy("user123", allergy_data)

    assert "allergy_id" in result
    mock_database.allergies.insert_one.assert_called_once()


@pytest.mark.integration
async def test_get_allergies_endpoint(mock_database, mock_patient_data):
    """Test GET /api/patients/allergies endpoint."""
    from app.services.patient_service import PatientService

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(
        return_value=[
            {
                "allergy_id": "AL1",
                "patient_id": "PT123",
                "allergy_name": "Penicillin",
                "severity": "severe",
                "reaction_description": "Anaphylactic reaction",
                "created_at": datetime.utcnow(),
            }
        ]
    )
    mock_database.allergies.find = Mock(return_value=mock_cursor)

    service = PatientService(mock_database)
    result = await service.get_allergies("user123")

    assert len(result) == 1
    assert result[0]["allergy_name"] == "Penicillin"


@pytest.mark.integration
async def test_delete_allergy_endpoint(mock_database, mock_patient_data):
    """Test DELETE /api/patients/allergies/{allergy_id} endpoint."""
    from app.services.patient_service import PatientService

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.allergies.delete_one = AsyncMock(return_value=Mock(deleted_count=1))

    service = PatientService(mock_database)
    result = await service.delete_allergy("user123", "AL1")

    assert result["deletion_status"] == "success"
    mock_database.allergies.delete_one.assert_called_once()


@pytest.mark.integration
async def test_get_health_score_endpoint(mock_database, mock_patient_data):
    """Test GET /api/patients/health-score endpoint."""
    from app.services.health_score_service import HealthScoreService

    # Setup mock database responses
    mock_database.medical_history.count_documents = AsyncMock(return_value=2)
    mock_database.medical_history.find = Mock(
        return_value=AsyncMock(
            to_list=AsyncMock(
                return_value=[
                    {"treatment_notes": "Take medication pills twice daily"},
                    {"treatment_notes": "No medicine required"},
                ]
            )
        )
    )

    service = HealthScoreService(mock_database)

    result = await service.calculate_health_score("PT123", mock_patient_data)

    assert 0 <= result.health_score <= 100
    assert result.score_components.bmi > 0
    assert result.score_components.active_conditions_count == 2
    assert isinstance(result.score_components.medication_count, int)


@pytest.mark.integration
async def test_add_insurance_new_endpoint(mock_database, mock_patient_data):
    """Test POST /api/patients/insurance endpoint (new insurance)."""
    from app.services.patient_service import PatientService
    from app.models.patient import InsuranceCreate

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.insurance.find_one = AsyncMock(return_value=None)
    mock_database.insurance.insert_one = AsyncMock()

    service = PatientService(mock_database)
    insurance_data = InsuranceCreate(
        provider_name="BlueCross",
        policy_number="BC123456",
        coverage_type="premium",
        expiry_date=(datetime.utcnow() + timedelta(days=365)).isoformat(),
    )

    result = await service.add_insurance("user123", insurance_data)

    assert "insurance_id" in result
    mock_database.insurance.insert_one.assert_called_once()


@pytest.mark.integration
async def test_add_insurance_update_endpoint(mock_database, mock_patient_data, mock_insurance_data):
    """Test POST /api/patients/insurance endpoint (update existing)."""
    from app.services.patient_service import PatientService
    from app.models.patient import InsuranceCreate

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.insurance.find_one = AsyncMock(return_value=mock_insurance_data)
    mock_database.insurance.update_one = AsyncMock()

    service = PatientService(mock_database)
    insurance_data = InsuranceCreate(
        provider_name="BlueCross Updated",
        policy_number="BC123456",
        coverage_type="standard",
        expiry_date=(datetime.utcnow() + timedelta(days=365)).isoformat(),
    )

    result = await service.add_insurance("user123", insurance_data)

    assert "insurance_id" in result
    mock_database.insurance.update_one.assert_called_once()


@pytest.mark.integration
async def test_get_insurance_endpoint(mock_database, mock_patient_data, mock_insurance_data):
    """Test GET /api/patients/insurance endpoint."""
    from app.services.patient_service import PatientService

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.insurance.find_one = AsyncMock(return_value=mock_insurance_data)

    service = PatientService(mock_database)
    result = await service.get_insurance("user123")

    assert result is not None
    assert result["insurance_id"] == "IN20240101120000001"
    assert result["provider_name"] == "BlueCross BlueShield"


# Error handling tests


@pytest.mark.integration
async def test_register_duplicate_patient_fails(mock_database):
    """Test that duplicate patient registration fails."""
    from app.services.patient_service import PatientService
    from app.models.patient import PatientCreate

    mock_database.patients.find_one = AsyncMock(return_value={"user_id": "user123"})

    service = PatientService(mock_database)
    patient_data = PatientCreate(
        user_id="user123",
        date_of_birth="1990-01-01",
        gender="male",
        blood_type="O+",
        height_cm=175.0,
        weight_kg=70.0,
        emergency_contact_name="Jane Doe",
        emergency_contact_phone="1234567890",
    )

    with pytest.raises(ValueError, match="Patient profile already exists"):
        await service.register_patient(patient_data)


@pytest.mark.integration
async def test_get_nonexistent_patient_profile_fails(mock_database):
    """Test getting non-existent patient profile returns None."""
    from app.services.patient_service import PatientService

    mock_database.patients.find_one = AsyncMock(return_value=None)

    service = PatientService(mock_database)
    result = await service.get_patient_by_user_id("nonexistent")

    assert result is None


@pytest.mark.integration
async def test_get_nonexistent_insurance_fails(mock_database, mock_patient_data):
    """Test getting non-existent insurance returns None."""
    from app.services.patient_service import PatientService

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.insurance.find_one = AsyncMock(return_value=None)

    service = PatientService(mock_database)
    result = await service.get_insurance("user123")

    assert result is None


@pytest.mark.integration
async def test_delete_nonexistent_allergy_fails(mock_database, mock_patient_data):
    """Test deleting non-existent allergy raises ValueError."""
    from app.services.patient_service import PatientService

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.allergies.delete_one = AsyncMock(return_value=Mock(deleted_count=0))

    service = PatientService(mock_database)

    with pytest.raises(ValueError, match="Allergy not found"):
        await service.delete_allergy("user123", "nonexistent")


@pytest.mark.integration
async def test_update_nonexistent_medical_history_fails(mock_database, mock_patient_data):
    """Test updating non-existent medical history raises ValueError."""
    from app.services.patient_service import PatientService
    from app.models.patient import MedicalHistoryUpdate

    mock_database.patients.find_one = AsyncMock(return_value=mock_patient_data)
    mock_database.medical_history.update_one = AsyncMock(return_value=Mock(matched_count=0))

    service = PatientService(mock_database)
    update_data = MedicalHistoryUpdate(status="resolved")

    with pytest.raises(ValueError, match="Medical history not found"):
        await service.update_medical_history("user123", "nonexistent", update_data)


@pytest.mark.integration
async def test_add_medical_history_for_nonexistent_patient_fails(mock_database):
    """Test adding medical history for non-existent patient raises ValueError."""
    from app.services.patient_service import PatientService
    from app.models.patient import MedicalHistoryCreate

    mock_database.patients.find_one = AsyncMock(return_value=None)

    service = PatientService(mock_database)
    history_data = MedicalHistoryCreate(
        condition_name="Hypertension",
        diagnosis_date="2021-01-01",
        status="active",
        treatment_notes="ACE inhibitors",
    )

    with pytest.raises(ValueError, match="Patient not found"):
        await service.add_medical_history("nonexistent", history_data)


@pytest.mark.integration
async def test_add_allergy_for_nonexistent_patient_fails(mock_database):
    """Test adding allergy for non-existent patient raises ValueError."""
    from app.services.patient_service import PatientService
    from app.models.patient import AllergyCreate

    mock_database.patients.find_one = AsyncMock(return_value=None)

    service = PatientService(mock_database)
    allergy_data = AllergyCreate(allergy_name="Peanuts", severity="severe", reaction_description="Anaphylaxis")

    with pytest.raises(ValueError, match="Patient not found"):
        await service.add_allergy("nonexistent", allergy_data)
