"""Unit tests for appointment management."""
# pylint: disable=redefined-outer-name,unused-argument
from datetime import datetime, timedelta

import pytest

from app.services.appointment_service import AppointmentService
from app.services.availability_service import AvailabilityService
from app.models.appointment import (
    AppointmentUpdateRequest,
    AppointmentStatus,
)


@pytest.fixture
async def appointment_service(db):
    """Create appointment service instance."""
    return AppointmentService(db)


@pytest.fixture
async def availability_service(db):
    """Create availability service instance."""
    return AvailabilityService(db)


@pytest.fixture
async def test_patient(db):
    """Create a test patient in database."""
    patient_data = {
        "patient_id": "PT123456",
        "user_id": "user123",
        "full_name": "Test Patient",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "blood_type": "O+",
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "emergency_contact_name": "Emergency Contact",
        "emergency_contact_phone": "+1234567890",
        "created_at": datetime.utcnow(),
        "is_active": True,
    }
    await db.patients.insert_one(patient_data)
    return patient_data


@pytest.fixture
async def test_doctor(db):
    """Create a test doctor in database."""
    doctor_data = {
        "doctor_id": "DOC123456",
        "user_id": "doctor123",
        "full_name": "Dr. Test Doctor",
        "specialization": "General Medicine",
        "created_at": datetime.utcnow(),
        "is_active": True,
    }
    await db.doctors.insert_one(doctor_data)
    return doctor_data


@pytest.fixture
async def test_appointment(db, test_patient, test_doctor):
    """Create a test appointment in database."""
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    appointment_data = {
        "appointment_id": "APT123456",
        "patient_id": test_patient["patient_id"],
        "doctor_id": test_doctor["doctor_id"],
        "appointment_date": tomorrow,
        "appointment_time": "10:00",
        "duration_minutes": 30,
        "reason": "Routine checkup",
        "notes": "Test notes",
        "status": AppointmentStatus.pending.value,
        "cancellation_reason": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "cancelled_at": None,
    }
    await db.appointments.insert_one(appointment_data)
    return appointment_data


@pytest.mark.asyncio
async def test_book_appointment_success(appointment_service, test_patient, test_doctor, db):
    """Test successful appointment booking."""
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

    result = await appointment_service.book_appointment(
        patient_id=test_patient["patient_id"],
        doctor_id=test_doctor["doctor_id"],
        appointment_date=tomorrow,
        appointment_time="14:00",
        reason="Annual checkup",
        notes="First appointment",
    )

    assert result["status"] == AppointmentStatus.pending.value
    assert "appointment_id" in result
    assert result["confirmation_details"]["appointment_date"] == tomorrow
    assert result["confirmation_details"]["appointment_time"] == "14:00"

    appointment = await db.appointments.find_one({"appointment_id": result["appointment_id"]})
    assert appointment is not None
    assert appointment["patient_id"] == test_patient["patient_id"]
    assert appointment["doctor_id"] == test_doctor["doctor_id"]


@pytest.mark.asyncio
async def test_book_appointment_past_date(appointment_service, test_patient, test_doctor):
    """Test rejection of past date appointments."""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    with pytest.raises(ValueError, match="must be scheduled in the future"):
        await appointment_service.book_appointment(
            patient_id=test_patient["patient_id"],
            doctor_id=test_doctor["doctor_id"],
            appointment_date=yesterday,
            appointment_time="10:00",
            reason="Test",
        )


@pytest.mark.asyncio
async def test_book_appointment_double_booking(appointment_service, test_patient, test_doctor, test_appointment):
    """Test prevention of double booking."""
    with pytest.raises(ValueError, match="already booked"):
        await appointment_service.book_appointment(
            patient_id=test_patient["patient_id"],
            doctor_id=test_doctor["doctor_id"],
            appointment_date=test_appointment["appointment_date"],
            appointment_time=test_appointment["appointment_time"],
            reason="Test",
        )


@pytest.mark.asyncio
async def test_get_appointment_by_patient(appointment_service, test_appointment, test_patient):
    """Test getting appointment details by patient."""
    appointment = await appointment_service.get_appointment(
        appointment_id=test_appointment["appointment_id"],
        user_id="user123",
        user_role="patient",
    )

    assert appointment is not None
    assert appointment["appointment_id"] == test_appointment["appointment_id"]
    assert appointment["patient_id"] == test_patient["patient_id"]


@pytest.mark.asyncio
async def test_get_appointment_unauthorized(appointment_service, test_appointment):
    """Test unauthorized access to appointment."""
    appointment = await appointment_service.get_appointment(
        appointment_id=test_appointment["appointment_id"],
        user_id="different_user",
        user_role="patient",
    )

    assert appointment is None


@pytest.mark.asyncio
async def test_get_patient_appointments(appointment_service, test_patient, test_appointment):
    """Test listing patient appointments."""
    result = await appointment_service.get_patient_appointments(
        patient_id=test_patient["patient_id"],
        limit=10,
        offset=0,
    )

    assert result["total"] >= 1
    assert len(result["appointments"]) >= 1
    assert result["appointments"][0]["appointment_id"] == test_appointment["appointment_id"]


@pytest.mark.asyncio
async def test_get_patient_appointments_with_status_filter(appointment_service, test_patient, test_appointment):
    """Test filtering appointments by status."""
    result = await appointment_service.get_patient_appointments(
        patient_id=test_patient["patient_id"],
        status=AppointmentStatus.pending.value,
        limit=10,
        offset=0,
    )

    assert result["total"] >= 1
    for appointment in result["appointments"]:
        assert appointment["status"] == AppointmentStatus.pending.value


@pytest.mark.asyncio
async def test_update_appointment_notes(appointment_service, test_appointment):
    """Test updating appointment notes."""
    update_data = AppointmentUpdateRequest(notes="Updated notes")

    updated = await appointment_service.update_appointment(
        appointment_id=test_appointment["appointment_id"],
        update_data=update_data,
    )

    assert updated is not None
    assert updated["notes"] == "Updated notes"


@pytest.mark.asyncio
async def test_update_appointment_reschedule(appointment_service, test_appointment, test_doctor):
    """Test rescheduling appointment."""
    new_date = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")
    update_data = AppointmentUpdateRequest(
        appointment_date=new_date,
        appointment_time="15:00",
    )

    updated = await appointment_service.update_appointment(
        appointment_id=test_appointment["appointment_id"],
        update_data=update_data,
    )

    assert updated is not None
    assert updated["appointment_date"] == new_date
    assert updated["appointment_time"] == "15:00"


@pytest.mark.asyncio
async def test_update_appointment_invalid_time(appointment_service, test_appointment):
    """Test updating appointment with past time."""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    update_data = AppointmentUpdateRequest(
        appointment_date=yesterday,
        appointment_time="10:00",
    )

    with pytest.raises(ValueError, match="must be scheduled in the future"):
        await appointment_service.update_appointment(
            appointment_id=test_appointment["appointment_id"],
            update_data=update_data,
        )


@pytest.mark.asyncio
async def test_cancel_appointment_success(appointment_service, test_appointment):
    """Test successful appointment cancellation."""
    result = await appointment_service.cancel_appointment(
        appointment_id=test_appointment["appointment_id"],
        cancellation_reason="Patient request",
    )

    assert result["status"] == AppointmentStatus.cancelled.value
    assert result["appointment_id"] == test_appointment["appointment_id"]
    assert "cancelled_at" in result


@pytest.mark.asyncio
async def test_cancel_nonexistent_appointment(appointment_service):
    """Test cancelling non-existent appointment."""
    with pytest.raises(ValueError, match="not found"):
        await appointment_service.cancel_appointment(
            appointment_id="NONEXISTENT",
            cancellation_reason="Test",
        )


@pytest.mark.asyncio
async def test_cancel_already_cancelled_appointment(appointment_service, test_appointment, db):
    """Test cancelling already cancelled appointment."""
    await db.appointments.update_one(
        {"appointment_id": test_appointment["appointment_id"]},
        {"$set": {"status": AppointmentStatus.cancelled.value}},
    )

    with pytest.raises(ValueError, match="Can only cancel pending or confirmed"):
        await appointment_service.cancel_appointment(
            appointment_id=test_appointment["appointment_id"],
            cancellation_reason="Test",
        )


@pytest.mark.asyncio
async def test_reschedule_appointment_success(appointment_service, test_appointment):
    """Test successful appointment rescheduling."""
    new_date = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")

    updated = await appointment_service.reschedule_appointment(
        appointment_id=test_appointment["appointment_id"],
        new_date=new_date,
        new_time="16:00",
    )

    assert updated is not None
    assert updated["appointment_date"] == new_date
    assert updated["appointment_time"] == "16:00"


@pytest.mark.asyncio
async def test_reschedule_appointment_past_date(appointment_service, test_appointment):
    """Test rescheduling to past date."""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    with pytest.raises(ValueError, match="must be scheduled in the future"):
        await appointment_service.reschedule_appointment(
            appointment_id=test_appointment["appointment_id"],
            new_date=yesterday,
            new_time="10:00",
        )


@pytest.mark.asyncio
async def test_get_appointment_history(appointment_service, test_patient, test_appointment):
    """Test getting appointment history."""
    result = await appointment_service.get_appointment_history(
        patient_id=test_patient["patient_id"],
        limit=10,
        offset=0,
    )

    assert result["total"] >= 1
    assert len(result["appointments"]) >= 1
    assert result["limit"] == 10
    assert result["offset"] == 0


@pytest.mark.asyncio
async def test_appointment_pagination(appointment_service, test_patient, test_doctor, db):
    """Test appointment list pagination."""
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

    for i in range(5):
        await appointment_service.book_appointment(
            patient_id=test_patient["patient_id"],
            doctor_id=test_doctor["doctor_id"],
            appointment_date=tomorrow,
            appointment_time=f"{10 + i}:00",
            reason=f"Appointment {i}",
        )

    result_page1 = await appointment_service.get_patient_appointments(
        patient_id=test_patient["patient_id"],
        limit=3,
        offset=0,
    )

    result_page2 = await appointment_service.get_patient_appointments(
        patient_id=test_patient["patient_id"],
        limit=3,
        offset=3,
    )

    assert result_page1["total"] >= 5
    assert len(result_page1["appointments"]) == 3
    assert len(result_page2["appointments"]) >= 2


@pytest.mark.asyncio
async def test_validate_appointment_time_future(availability_service):
    """Test validating future appointment time."""
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    is_valid = await availability_service.validate_appointment_time(tomorrow, "10:00")
    assert is_valid is True


@pytest.mark.asyncio
async def test_validate_appointment_time_past(availability_service):
    """Test validating past appointment time."""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    is_valid = await availability_service.validate_appointment_time(yesterday, "10:00")
    assert is_valid is False


@pytest.mark.asyncio
async def test_validate_appointment_time_invalid_format(availability_service):
    """Test validating invalid time format."""
    is_valid = await availability_service.validate_appointment_time("invalid-date", "10:00")
    assert is_valid is False
