"""Minimal test suite for appointment booking system."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from app.services.appointment_service import AppointmentService
from app.models.appointment import AppointmentCreate, CancellationRequest, RescheduleRequest


@pytest.fixture
def mock_database():
    """Create mock database for testing."""
    mock_db = Mock()
    mock_db.appointments = AsyncMock()
    mock_db.appointments.find = AsyncMock(return_value=[])
    mock_db.appointments.find_one = AsyncMock(return_value=None)
    mock_db.appointments.insert_one = AsyncMock(return_value=Mock(inserted_id="test_id"))
    mock_db.appointments.update_one = AsyncMock(return_value=Mock(modified_count=1))
    mock_db.appointment_slots = AsyncMock()
    mock_db.reschedule_history = AsyncMock()
    mock_db.appointment_reminders = AsyncMock()
    return mock_db


@pytest.fixture
def appointment_service(mock_database):
    """Create appointment service instance for testing."""
    return AppointmentService(mock_database)


@pytest.fixture
def sample_appointment_data():
    """Sample appointment data for testing."""
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return AppointmentCreate(
        doctor_id="doctor_123",
        appointment_date=future_date,
        appointment_time="10:00",
        duration_minutes=30,
        notes="Test appointment",
        consultation_type="general",
    )


class TestConflictDetection:
    """Test conflict detection functionality."""

    @pytest.mark.asyncio
    async def test_no_conflict_different_times(self, appointment_service):
        """Test no conflict when appointments are at different times."""
        result = await appointment_service.check_conflict_detection(
            doctor_id="doctor_123", appointment_date="2025-12-25", appointment_time="10:00", duration_minutes=30
        )

        assert result["conflict_found"] is False
        assert len(result["conflicting_appointments"]) == 0

    @pytest.mark.asyncio
    async def test_conflict_same_time(self, appointment_service):
        """Test conflict when appointments are at the same time."""
        existing_appointment = {
            "appointment_id": "apt_456",
            "doctor_id": "doctor_123",
            "appointment_date": "2025-12-25",
            "appointment_time": "10:00",
            "duration_minutes": 30,
            "status": "scheduled",
        }

        appointment_service.appointments_collection.find = AsyncMock(return_value=[existing_appointment])

        result = await appointment_service.check_conflict_detection(
            doctor_id="doctor_123", appointment_date="2025-12-25", appointment_time="10:00", duration_minutes=30
        )

        assert result["conflict_found"] is True
        assert len(result["conflicting_appointments"]) == 1


class TestRefundCalculation:
    """Test refund calculation logic."""

    @pytest.mark.asyncio
    async def test_100_percent_refund_24_hours_before(self, appointment_service):
        """Test 100% refund when cancelled 24+ hours before."""
        future_datetime = datetime.now() + timedelta(hours=48)
        appointment = {
            "appointment_id": "apt_123",
            "appointment_date": future_datetime.strftime("%Y-%m-%d"),
            "appointment_time": future_datetime.strftime("%H:%M"),
            "status": "scheduled",
        }

        appointment_service.appointments_collection.find_one = AsyncMock(return_value=appointment)

        refund_amount, refund_percentage, policy = await appointment_service.calculate_refund("apt_123")

        assert refund_percentage == 100.0
        assert refund_amount == 100.0
        assert "100% refund" in policy

    @pytest.mark.asyncio
    async def test_50_percent_refund_6_to_24_hours_before(self, appointment_service):
        """Test 50% refund when cancelled between 6-24 hours before."""
        future_datetime = datetime.now() + timedelta(hours=12)
        appointment = {
            "appointment_id": "apt_123",
            "appointment_date": future_datetime.strftime("%Y-%m-%d"),
            "appointment_time": future_datetime.strftime("%H:%M"),
            "status": "scheduled",
        }

        appointment_service.appointments_collection.find_one = AsyncMock(return_value=appointment)

        refund_amount, refund_percentage, policy = await appointment_service.calculate_refund("apt_123")

        assert refund_percentage == 50.0
        assert refund_amount == 50.0
        assert "50% refund" in policy

    @pytest.mark.asyncio
    async def test_0_percent_refund_less_than_6_hours_before(self, appointment_service):
        """Test 0% refund when cancelled less than 6 hours before."""
        future_datetime = datetime.now() + timedelta(hours=3)
        appointment = {
            "appointment_id": "apt_123",
            "appointment_date": future_datetime.strftime("%Y-%m-%d"),
            "appointment_time": future_datetime.strftime("%H:%M"),
            "status": "scheduled",
        }

        appointment_service.appointments_collection.find_one = AsyncMock(return_value=appointment)

        refund_amount, refund_percentage, policy = await appointment_service.calculate_refund("apt_123")

        assert refund_percentage == 0.0
        assert refund_amount == 0.0
        assert "0% refund" in policy


class TestBookingFlow:
    """Test appointment booking functionality."""

    @pytest.mark.asyncio
    async def test_successful_booking(self, appointment_service, sample_appointment_data):
        """Test successful appointment booking."""
        # Mock conflict detection
        appointment_service.check_conflict_detection = AsyncMock(return_value={"conflict_found": False})

        # Mock appointment creation
        appointment_service.appointments_collection.insert_one = AsyncMock()

        # Mock reminder scheduling
        appointment_service._schedule_reminders = AsyncMock()

        # Mock response conversion
        appointment_service._convert_to_response = AsyncMock(
            return_value=Mock(appointment_id="new_apt_123", status="scheduled")
        )

        result = await appointment_service.book_appointment("patient_456", sample_appointment_data)

        assert result.appointment_id == "new_apt_123"
        assert result.status == "scheduled"
        appointment_service.check_conflict_detection.assert_called_once()

    @pytest.mark.asyncio
    async def test_booking_conflict_rejection(self, appointment_service, sample_appointment_data):
        """Test booking rejection due to time conflict."""
        # Mock conflict detection - conflict found
        appointment_service.check_conflict_detection = AsyncMock(return_value={"conflict_found": True})

        with pytest.raises(ValueError, match="Time slot is not available"):
            await appointment_service.book_appointment("patient_456", sample_appointment_data)

        appointment_service.check_conflict_detection.assert_called_once()
        appointment_service.appointments_collection.insert_one.assert_not_called()


class TestCancellation:
    """Test appointment cancellation functionality."""

    @pytest.mark.asyncio
    async def test_successful_cancellation_with_refund(self, appointment_service):
        """Test successful appointment cancellation with refund."""
        future_datetime = datetime.now() + timedelta(hours=48)
        appointment = {
            "appointment_id": "apt_123",
            "appointment_date": future_datetime.strftime("%Y-%m-%d"),
            "appointment_time": future_datetime.strftime("%H:%M"),
            "status": "scheduled",
        }

        appointment_service.appointments_collection.find_one = AsyncMock(return_value=appointment)

        cancellation_data = CancellationRequest(reason="Emergency")

        appointment_service.calculate_refund = AsyncMock(return_value=(100.0, 100.0, "100% refund policy"))

        result = await appointment_service.cancel_appointment("apt_123", cancellation_data)

        assert result.status == "cancelled"
        assert result.refund_amount == 100.0
        assert result.refund_percentage == 100.0
        assert result.cancellation_reason == "Emergency"
        appointment_service.appointments_collection.update_one.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_appointment_not_found_error(self, appointment_service):
        """Test error handling for non-existent appointment."""
        appointment_service.appointments_collection.find_one = AsyncMock(return_value=None)

        cancellation_data = CancellationRequest(reason="Test")

        with pytest.raises(ValueError, match="Appointment not found"):
            await appointment_service.cancel_appointment("non_existent_id", cancellation_data)

    @pytest.mark.asyncio
    async def test_past_appointment_booking_rejection(self, appointment_service):
        """Test booking rejection for past appointment times."""
        past_appointment_data = AppointmentCreate(
            doctor_id="doctor_123", appointment_date="2020-01-01", appointment_time="10:00", duration_minutes=30
        )

        with pytest.raises(ValueError, match="Appointment must be scheduled for a future time"):
            await appointment_service.book_appointment("patient_456", past_appointment_data)

    @pytest.mark.asyncio
    async def test_completed_appointment_cancellation_rejection(self, appointment_service):
        """Test cancellation rejection for completed appointment."""
        appointment = {
            "appointment_id": "apt_123",
            "appointment_date": "2025-12-25",
            "appointment_time": "10:00",
            "status": "completed",
        }

        appointment_service.appointments_collection.find_one = AsyncMock(return_value=appointment)

        cancellation_data = CancellationRequest(reason="Changed mind")

        with pytest.raises(ValueError, match="Cannot cancel completed or already cancelled appointment"):
            await appointment_service.cancel_appointment("apt_123", cancellation_data)


# Integration test markers
pytestmark = pytest.mark.asyncio
