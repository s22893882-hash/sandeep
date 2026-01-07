"""Tests for patient management endpoints."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.patient import (
    PatientCreate,
    PatientUpdate,
    MedicalHistoryCreate,
    MedicalHistoryUpdate,
    AllergyCreate,
    InsuranceCreate,
)
from app.services.patient_service import PatientService
from app.services.health_score_service import HealthScoreService


@pytest.fixture
def mock_patient():
    """Create a mock patient."""
    return {
        "_id": ObjectId(),
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
def mock_medical_history():
    """Create a mock medical history record."""
    return {
        "_id": ObjectId(),
        "history_id": "MH20240101120000001",
        "patient_id": "PT20240101120000001",
        "condition_name": "Diabetes",
        "diagnosis_date": "2020-01-01",
        "status": "active",
        "treatment_notes": "Insulin therapy",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_allergy():
    """Create a mock allergy."""
    return {
        "_id": ObjectId(),
        "allergy_id": "AL20240101120000001",
        "patient_id": "PT20240101120000001",
        "allergy_name": "Penicillin",
        "severity": "severe",
        "reaction_description": "Anaphylaxis",
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_insurance():
    """Create a mock insurance."""
    return {
        "_id": ObjectId(),
        "insurance_id": "IN20240101120000001",
        "patient_id": "PT20240101120000001",
        "provider_name": "BlueCross",
        "policy_number": "BC123456",
        "coverage_type": "premium",
        "expiry_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_database():
    """Create a mock database."""
    db = Mock()
    db.patients = Mock()
    db.medical_history = Mock()
    db.allergies = Mock()
    db.insurance = Mock()
    return db


# Unit Tests for PatientService


@pytest.mark.unit
def test_patient_service_initialization(mock_database):
    """Test PatientService initialization."""
    service = PatientService(mock_database)
    assert service.db == mock_database


@pytest.mark.unit
async def test_register_patient_success(mock_database):
    """Test successful patient registration."""
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

    assert "patient_id" in result
    assert result["user_id"] == "user123"
    assert result["registration_status"] == "success"
    mock_database.patients.insert_one.assert_called_once()


@pytest.mark.unit
async def test_register_patient_duplicate_user(mock_database):
    """Test registering patient with existing user_id fails."""
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


@pytest.mark.unit
async def test_get_patient_by_user_id(mock_database, mock_patient):
    """Test retrieving patient by user ID."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)

    service = PatientService(mock_database)
    result = await service.get_patient_by_user_id("user123")

    assert result is not None
    assert result["user_id"] == "user123"
    assert result["patient_id"] == "PT20240101120000001"


@pytest.mark.unit
async def test_update_patient_success(mock_database, mock_patient):
    """Test updating patient profile."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)
    mock_database.patients.update_one = AsyncMock(return_value=Mock(matched_count=1))

    service = PatientService(mock_database)
    update_data = PatientUpdate(height_cm=180.0, weight_kg=75.0)

    result = await service.update_patient("user123", update_data)

    assert result is not None
    mock_database.patients.update_one.assert_called_once()


@pytest.mark.unit
async def test_add_medical_history_success(mock_database, mock_patient):
    """Test adding medical history record."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)
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
    assert result["patient_id"] == "PT20240101120000001"
    mock_database.medical_history.insert_one.assert_called_once()


@pytest.mark.unit
async def test_get_medical_history(mock_database, mock_patient):
    """Test retrieving medical history."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[{"history_id": "MH1", "condition_name": "Diabetes", "status": "active"}])
    mock_database.medical_history.find = Mock(return_value=mock_cursor)

    service = PatientService(mock_database)
    result = await service.get_medical_history("user123")

    assert len(result) == 1
    assert result[0]["condition_name"] == "Diabetes"


@pytest.mark.unit
async def test_update_medical_history_success(mock_database, mock_patient):
    """Test updating medical history record."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)
    mock_database.medical_history.update_one = AsyncMock(return_value=Mock(matched_count=1))
    mock_database.medical_history.find_one = AsyncMock(
        return_value={"history_id": "MH1", "status": "resolved", "treatment_notes": "Updated notes"}
    )

    service = PatientService(mock_database)
    update_data = MedicalHistoryUpdate(status="resolved", treatment_notes="Updated notes")

    result = await service.update_medical_history("user123", "MH1", update_data)

    assert result is not None
    mock_database.medical_history.update_one.assert_called_once()


@pytest.mark.unit
async def test_add_allergy_success(mock_database, mock_patient):
    """Test adding allergy record."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)
    mock_database.allergies.insert_one = AsyncMock()

    service = PatientService(mock_database)
    allergy_data = AllergyCreate(
        allergy_name="Peanuts", severity="severe", reaction_description="Swelling and difficulty breathing"
    )

    result = await service.add_allergy("user123", allergy_data)

    assert "allergy_id" in result
    assert result["patient_id"] == "PT20240101120000001"
    mock_database.allergies.insert_one.assert_called_once()


@pytest.mark.unit
async def test_get_allergies(mock_database, mock_patient):
    """Test retrieving allergies."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[{"allergy_id": "AL1", "allergy_name": "Penicillin", "severity": "severe"}])
    mock_database.allergies.find = Mock(return_value=mock_cursor)

    service = PatientService(mock_database)
    result = await service.get_allergies("user123")

    assert len(result) == 1
    assert result[0]["allergy_name"] == "Penicillin"


@pytest.mark.unit
async def test_delete_allergy_success(mock_database, mock_patient):
    """Test deleting allergy record."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)
    mock_database.allergies.delete_one = AsyncMock(return_value=Mock(deleted_count=1))

    service = PatientService(mock_database)
    result = await service.delete_allergy("user123", "AL1")

    assert result["deletion_status"] == "success"
    mock_database.allergies.delete_one.assert_called_once()


@pytest.mark.unit
async def test_add_insurance_new(mock_database, mock_patient):
    """Test adding new insurance."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)
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


@pytest.mark.unit
async def test_add_insurance_update_existing(mock_database, mock_patient, mock_insurance):
    """Test updating existing insurance."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)
    mock_database.insurance.find_one = AsyncMock(return_value=mock_insurance)
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


@pytest.mark.unit
async def test_get_insurance(mock_database, mock_patient, mock_insurance):
    """Test retrieving insurance."""
    mock_database.patients.find_one = AsyncMock(return_value=mock_patient)
    mock_database.insurance.find_one = AsyncMock(return_value=mock_insurance)

    service = PatientService(mock_database)
    result = await service.get_insurance("user123")

    assert result is not None
    assert result["provider_name"] == "BlueCross"


# Unit Tests for HealthScoreService


@pytest.mark.unit
def test_calculate_bmi():
    """Test BMI calculation."""
    mock_database = Mock()
    service = HealthScoreService(mock_database)

    bmi = service._calculate_bmi(175.0, 70.0)
    assert round(bmi, 2) == 22.86

    bmi = service._calculate_bmi(180.0, 80.0)
    assert round(bmi, 2) == 24.69


@pytest.mark.unit
def test_calculate_bmi_component():
    """Test BMI component score calculation."""
    mock_database = Mock()
    service = HealthScoreService(mock_database)

    # Optimal BMI (22.5)
    score = service._calculate_bmi_component(22.5)
    assert score == 100

    # Above optimal
    score = service._calculate_bmi_component(30.0)
    assert score == 85

    # Below optimal
    score = service._calculate_bmi_component(18.0)
    assert score == 91

    # Very high BMI (should give low score)
    score = service._calculate_bmi_component(50.0)
    assert score == 45.0

    # Extreme BMI (capped at 0)
    score = service._calculate_bmi_component(100.0)
    assert score == 0


@pytest.mark.unit
def test_calculate_conditions_component():
    """Test conditions component score calculation."""
    mock_database = Mock()
    service = HealthScoreService(mock_database)

    # No conditions
    score = service._calculate_conditions_component(0)
    assert score == 100

    # 2 conditions
    score = service._calculate_conditions_component(2)
    assert score == 70

    # 5 conditions
    score = service._calculate_conditions_component(5)
    assert score == 25

    # 10 conditions (capped at 0)
    score = service._calculate_conditions_component(10)
    assert score == 0


@pytest.mark.unit
def test_calculate_medications_component():
    """Test medications component score calculation."""
    mock_database = Mock()
    service = HealthScoreService(mock_database)

    # No medications
    score = service._calculate_medications_component(0)
    assert score == 100

    # 3 medications
    score = service._calculate_medications_component(3)
    assert score == 70

    # 10 medications (capped at 0)
    score = service._calculate_medications_component(10)
    assert score == 0


@pytest.mark.unit
def test_calculate_appointments_component():
    """Test appointments component score calculation."""
    mock_database = Mock()
    service = HealthScoreService(mock_database)

    # No appointments
    score = service._calculate_appointments_component(0)
    assert score == 0

    # 2 appointments
    score = service._calculate_appointments_component(2)
    assert score == 50

    # 4 appointments (full score)
    score = service._calculate_appointments_component(4)
    assert score == 100

    # 6 appointments (capped at 100)
    score = service._calculate_appointments_component(6)
    assert score == 100


@pytest.mark.unit
async def test_calculate_health_score(mock_database, mock_patient):
    """Test complete health score calculation."""
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

    result = await service.calculate_health_score("PT123", mock_patient)

    assert 0 <= result.health_score <= 100
    assert result.score_components.bmi > 0
    assert result.score_components.bmi_component > 0
    assert result.score_components.conditions_component > 0
    assert isinstance(result.score_components.medication_count, int)
    assert isinstance(result.score_components.active_conditions_count, int)
    assert result.score_components.appointments_component >= 0


@pytest.mark.unit
async def test_get_active_conditions_count(mock_database):
    """Test getting active conditions count."""
    mock_database.medical_history.count_documents = AsyncMock(return_value=3)

    service = HealthScoreService(mock_database)
    count = await service._get_active_conditions_count("PT123")

    assert count == 3
    mock_database.medical_history.count_documents.assert_called_once()


@pytest.mark.unit
async def test_get_medications_count(mock_database):
    """Test estimating medication count."""
    mock_database.medical_history.find = Mock(
        return_value=AsyncMock(
            to_list=AsyncMock(
                return_value=[
                    {"treatment_notes": "Take medication and pills"},
                    {"treatment_notes": "No medicine required"},
                    {"treatment_notes": "Dosage: 5mg tablet"},
                ]
            )
        )
    )

    service = HealthScoreService(mock_database)
    count = await service._get_medications_count("PT123")

    assert count >= 0


@pytest.mark.unit
async def test_get_recent_appointments_count(mock_database):
    """Test getting recent appointments count."""
    mock_database.medical_history.count_documents = AsyncMock(return_value=2)

    service = HealthScoreService(mock_database)
    count = await service._get_recent_appointments_count("PT123")

    assert count >= 0
    mock_database.medical_history.count_documents.assert_called_once()
