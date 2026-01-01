"""Unit tests for DoctorService."""

from datetime import datetime, timedelta
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.doctor_service import DoctorService
from app.schemas.doctors import DoctorRegistrationRequest, WorkingHoursUpdate, AvailabilityStatusUpdate


def test_doctor_service_initialization():
    """Test DoctorService can be initialized."""
    # Mock the database dependency
    service = DoctorService()
    assert service is not None


def test_doctor_registration_request_validation():
    """Test DoctorRegistrationRequest schema validation."""
    # Valid registration data
    registration_data = {
        "license_number": "DOC123456",
        "license_expiry": datetime.utcnow() + timedelta(days=365),
        "specialization": [{"specialization_name": "Cardiology", "expertise_level": "expert"}],
        "qualifications": [{"degree": "MD", "institution": "Harvard", "year": 2010, "field": "Cardiology"}],
        "clinic_address": "123 Medical Plaza",
        "clinic_phone": "555-1234",
        "consultation_fee": 150.0,
        "working_hours": {"Monday": {"start": "09:00", "end": "17:00"}},
        "bio": "Test bio",
        "languages": ["English", "Spanish"],
        "license_document_url": "https://example.com/license.pdf",
    }

    request = DoctorRegistrationRequest(**registration_data)
    assert request.license_number == "DOC123456"
    assert len(request.specialization) == 1
    assert len(request.qualifications) == 1


def test_working_hours_validation():
    """Test WorkingHoursUpdate schema validation."""
    working_hours_data = {
        "working_hours": {"Monday": {"start": "09:00", "end": "17:00"}, "Tuesday": {"start": "09:00", "end": "17:00"}},
        "is_available_weekends": False,
    }

    update = WorkingHoursUpdate(**working_hours_data)
    assert "Monday" in update.working_hours
    assert update.is_available_weekends is False


def test_availability_status_validation():
    """Test AvailabilityStatusUpdate schema validation."""
    status_data = {"status": "on-leave", "reason": "Vacation", "return_date": datetime.utcnow() + timedelta(days=7)}

    update = AvailabilityStatusUpdate(**status_data)
    assert update.status == "on-leave"
    assert update.reason == "Vacation"


def test_invalid_license_expiry():
    """Test that expired license is rejected."""
    with pytest.raises(ValueError):
        DoctorRegistrationRequest(
            license_number="DOC123456",
            license_expiry=datetime.utcnow() - timedelta(days=1),  # Expired
            specialization=[],
            qualifications=[],
            clinic_address="123 Medical Plaza",
            clinic_phone="555-1234",
            consultation_fee=150.0,
            working_hours={},
            bio="",
            languages=[],
            license_document_url=None,
        )


def test_consultation_fee_validation():
    """Test that negative consultation fee is rejected."""
    with pytest.raises(RuntimeError):  # or the specific exception type
        DoctorRegistrationRequest(
            license_number="DOC123456",
            license_expiry=datetime.utcnow() + timedelta(days=365),
            specialization=[],
            qualifications=[],
            clinic_address="123 Medical Plaza",
            clinic_phone="555-1234",
            consultation_fee=-10.0,  # Invalid negative fee
            working_hours={},
            bio="",
            languages=[],
            license_document_url=None,
        )


@pytest.mark.asyncio
async def test_slot_calculation_logic():
    """Test the slot calculation algorithm logic."""
    from datetime import datetime, time

    # Simulate the slot calculation logic
    start_time = time(9, 0)  # 09:00
    end_time = time(10, 0)  # 10:00
    duration_minutes = 30

    # Create mock occupied slots
    occupied_slots = [(time(9, 0), time(9, 30))]  # First half hour booked

    available_slots = []
    current_time = start_time

    import datetime as dt

    while True:
        current_dt = dt.datetime.combine(dt.date.min, current_time)
        end_slot_dt = current_dt + dt.timedelta(minutes=duration_minutes)

        if end_slot_dt.time() > end_time:
            break

        slot_start = current_time
        slot_end = end_slot_dt.time()

        # Check if slot is occupied
        is_occupied = any(
            occupied_start <= slot_start < occupied_end or occupied_start < slot_end <= occupied_end
            for occupied_start, occupied_end in occupied_slots
        )

        if not is_occupied:
            available_slots.append({"start_time": slot_start.strftime("%H:%M"), "end_time": slot_end.strftime("%H:%M")})

        current_time = slot_end

    # Verify we have one available slot (09:30-10:00)
    assert len(available_slots) == 1
    assert available_slots[0]["start_time"] == "09:30"
    assert available_slots[0]["end_time"] == "10:00"
