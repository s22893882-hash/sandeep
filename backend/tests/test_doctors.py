"""
Comprehensive test suite for doctor management system.
Tests all doctor APIs including profile management, verification, and scheduling.
"""

from datetime import datetime, timedelta
import pytest
from app.core.security import create_access_token
from app.services.doctor_service import DoctorService
from app.core.database import get_db
from app.schemas.doctors import DoctorRegistrationRequest, WorkingHoursUpdate


class TestDoctorRegistration:
    """Test suite for doctor registration and onboarding."""

    async def test_doctor_registration_success(self, test_db):
        """Test successful doctor registration."""
        # Create test user
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )
        user_id = str(user_result.inserted_id)

        # Create registration data
        registration_data = DoctorRegistrationRequest(
            license_number="DOC123456",
            license_expiry=datetime.utcnow() + timedelta(days=365),
            specialization=[{"specialization_name": "Cardiology", "expertise_level": "expert"}],
            qualifications=[{"degree": "MD", "institution": "Harvard Medical School", "year": 2010, "field": "Cardiology"}],
            clinic_address="123 Medical Plaza, Suite 200, Boston, MA 02101",
            clinic_phone="617-555-0123",
            consultation_fee=150.0,
            working_hours={
                "Monday": {"start": "09:00", "end": "17:00"},
                "Tuesday": {"start": "09:00", "end": "17:00"},
                "Wednesday": {"start": "09:00", "end": "17:00"},
                "Thursday": {"start": "09:00", "end": "17:00"},
                "Friday": {"start": "09:00", "end": "17:00"},
            },
            bio="Experienced cardiologist with 10+ years in practice",
            languages=["English", "Spanish"],
            license_document_url="https://example.com/license.pdf",
        )

        service = DoctorService()
        result = await service.register_doctor(user_id, registration_data)

        assert "doctor_id" in result
        assert result["message"] == "Profile submitted for verification"

        # Verify database
        doctor = await test_db.doctors.find_one({"_id": result["doctor_id"]})
        assert doctor is not None
        assert doctor["license_number"] == "DOC123456"
        assert doctor["is_verified"] is False
        assert doctor["is_active"] is True

    async def test_doctor_registration_duplicate_user(self, test_db):
        """Test doctor registration with duplicate user."""
        # Create test user and existing doctor profile
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )
        user_id = str(user_result.inserted_id)

        await test_db.doctors.insert_one(
            {"user_id": user_id, "license_number": "DOC123456", "is_verified": False, "is_active": True}
        )

        registration_data = DoctorRegistrationRequest(
            license_number="DOC789012",
            license_expiry=datetime.utcnow() + timedelta(days=365),
            specialization=[{"specialization_name": "Cardiology", "expertise_level": "expert"}],
            qualifications=[],
            clinic_address="123 Medical Plaza",
            clinic_phone="617-555-0123",
            consultation_fee=150.0,
            working_hours={"Monday": {"start": "09:00", "end": "17:00"}},
            bio="",
            languages=[],
            license_document_url=None,
        )

        service = DoctorService()

        with pytest.raises(ValueError, match="Doctor profile already exists"):
            await service.register_doctor(user_id, registration_data)

    async def test_doctor_registration_expired_license(self):
        """Test doctor registration with expired license."""
        registration_data = DoctorRegistrationRequest(
            license_number="DOC123456",
            license_expiry=datetime.utcnow() - timedelta(days=1),  # Expired
            specialization=[{"specialization_name": "Cardiology", "expertise_level": "expert"}],
            qualifications=[],
            clinic_address="123 Medical Plaza",
            clinic_phone="617-555-0123",
            consultation_fee=150.0,
            working_hours={"Monday": {"start": "09:00", "end": "17:00"}},
            bio="",
            languages=[],
            license_document_url=None,
        )

        with pytest.raises(ValueError, match="License has expired"):
            DoctorRegistrationRequest(**registration_data.dict())


class TestDoctorProfile:
    """Test suite for doctor profile management."""

    async def test_get_doctor_profile_success(self, test_db):
        """Test getting doctor profile successfully."""
        # Create test user
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )
        user_id = str(user_result.inserted_id)

        # Create test doctor
        doctor_result = await test_db.doctors.insert_one(
            {
                "user_id": user_id,
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [{"name": "Cardiology", "expertise_level": "expert"}],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": True,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )
        doctor_id = str(doctor_result.inserted_id)

        service = DoctorService()
        profile = await service.get_doctor_profile(doctor_id)

        assert profile["doctor_id"] == doctor_id
        assert profile["user"]["name"] == "Dr. John Smith"
        assert profile["license_number"] == "DOC123456"
        assert profile["is_verified"] is True

    async def test_get_doctor_profile_not_found(self):
        """Test getting non-existent doctor profile."""
        service = DoctorService()

        with pytest.raises(ValueError, match="Doctor not found"):
            await service.get_doctor_profile("nonexistent_id")

    async def test_update_doctor_profile_success(self, test_db):
        """Test updating doctor profile successfully."""
        # Create test user and doctor
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )
        user_id = str(user_result.inserted_id)

        doctor_result = await test_db.doctors.insert_one(
            {
                "user_id": user_id,
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": True,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )

        service = DoctorService()
        update_data = {"bio": "Updated bio", "consultation_fee": 200.0}
        result = await service.update_doctor_profile(user_id, update_data)

        assert result["bio"] == "Updated bio"
        assert result["consultation_fee"] == 200.0

    async def test_update_doctor_profile_license_reset_verification(self, test_db):
        """Test that updating license resets verification."""
        # Create test user and doctor
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )
        user_id = str(user_result.inserted_id)

        await test_db.doctors.insert_one(
            {
                "user_id": user_id,
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": True,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )

        service = DoctorService()
        update_data = {"license_number": "DOC789012"}
        result = await service.update_doctor_profile(user_id, update_data)

        assert result["license_number"] == "DOC789012"
        assert result["is_verified"] is False


class TestDoctorVerification:
    """Test suite for doctor verification."""

    async def test_verify_doctor_success(self, test_db):
        """Test successful doctor verification."""
        # Create test doctor
        doctor_result = await test_db.doctors.insert_one(
            {
                "user_id": "user123",
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": False,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )
        doctor_id = str(doctor_result.inserted_id)

        service = DoctorService()
        result = await service.verify_doctor(doctor_id, True)

        assert result["message"] == "Doctor verified: True"

        # Verify in database
        doctor = await test_db.doctors.find_one({"_id": doctor_id})
        assert doctor["is_verified"] is True
        assert doctor["verification_date"] is not None

    async def test_reject_doctor_verification(self, test_db):
        """Test rejecting doctor verification."""
        # Create test doctor
        doctor_result = await test_db.doctors.insert_one(
            {
                "user_id": "user123",
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": False,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )
        doctor_id = str(doctor_result.inserted_id)

        service = DoctorService()
        result = await service.verify_doctor(doctor_id, False, "Insufficient documentation")

        assert "rejected" in result["message"].lower()

        # Verify in database
        doctor = await test_db.doctors.find_one({"_id": doctor_id})
        assert doctor["is_verified"] is False
        assert doctor.get("rejection_reason") == "Insufficient documentation"


class TestWorkingHours:
    """Test suite for working hours management."""

    async def test_update_working_hours_success(self, test_db):
        """Test updating working hours successfully."""
        # Create test user and doctor
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )
        user_id = str(user_result.inserted_id)

        await test_db.doctors.insert_one(
            {
                "user_id": user_id,
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": False,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )

        service = DoctorService()
        working_hours_data = {
            "working_hours": {"Monday": {"start": "09:00", "end": "17:00"}, "Tuesday": {"start": "09:00", "end": "17:00"}},
            "is_available_weekends": False,
        }

        result = await service.update_working_hours(user_id, working_hours_data)

        assert "Monday" in result["working_hours"]
        assert result["is_available_weekends"] is False

    async def test_invalid_working_hours_format(self, test_db):
        """Test updating with invalid time format."""
        # Create test user and doctor
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )
        user_id = str(user_result.inserted_id)

        await test_db.doctors.insert_one(
            {
                "user_id": user_id,
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": False,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )

        from pydantic import ValidationError

        # Test invalid time format
        with pytest.raises(ValidationError):
            WorkingHoursUpdate(
                **{
                    "working_hours": {"Monday": {"start": "25:00", "end": "17:00"}},
                    "is_available_weekends": False,
                }
            )


class TestAvailability:
    """Test suite for availability management."""

    async def test_update_availability_status_success(self, test_db):
        """Test updating availability status successfully."""
        # Create test user and doctor
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )
        user_id = str(user_result.inserted_id)

        await test_db.doctors.insert_one(
            {
                "user_id": user_id,
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": False,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )

        service = DoctorService()
        status_data = {"status": "on-leave", "reason": "Vacation", "return_date": datetime.utcnow() + timedelta(days=7)}

        result = await service.update_availability_status(user_id, status_data)

        assert result["status"] == "on-leave"
        assert result["reason"] == "Vacation"
        assert result["return_date"] is not None


class TestAvailableSlots:
    """Test suite for available slots calculation."""

    async def test_get_available_slots_success(self, test_db):
        """Test getting available slots successfully."""
        # Create test doctor
        doctor_result = await test_db.doctors.insert_one(
            {
                "user_id": "user123",
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {"Monday": {"start": "09:00", "end": "17:00"}},
                "is_verified": False,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )
        doctor_id = str(doctor_result.inserted_id)

        service = DoctorService()
        target_date = datetime.utcnow()

        # Set date to Monday for testing
        while target_date.weekday() != 0:  # 0 = Monday
            target_date += timedelta(days=1)

        slots = await service.get_available_slots(doctor_id, target_date)

        assert len(slots) > 0
        assert "start_time" in slots[0]
        assert "end_time" in slots[0]

    async def test_get_available_slots_with_appointments(self, test_db):
        """Test getting available slots with existing appointments."""
        # Create test doctor
        doctor_result = await test_db.doctors.insert_one(
            {
                "user_id": "user123",
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {"Monday": {"start": "09:00", "end": "10:00"}},
                "is_verified": False,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )
        doctor_id = str(doctor_result.inserted_id)

        # Create test date (Monday)
        target_date = datetime.utcnow()
        while target_date.weekday() != 0:
            target_date += timedelta(days=1)

        # Book an appointment
        await test_db.appointments.insert_one(
            {
                "doctor_id": doctor_id,
                "patient_id": "patient123",
                "date": target_date,
                "start_time": "09:00",
                "end_time": "09:30",
                "status": "scheduled",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        service = DoctorService()
        slots = await service.get_available_slots(doctor_id, target_date)

        # Should return available slots (excluding booked slot)
        booked_slot_start = "09:00"
        slotted_start_times = [slot["start_time"] for slot in slots]
        assert booked_slot_start not in slotted_start_times


class TestDoctorSearch:
    """Test suite for doctor search and filtering."""

    async def test_search_doctors_by_specialization(self, test_db):
        """Test searching doctors by specialization."""
        # Create test users and doctors
        user1_result = await test_db.users.insert_one(
            {
                "email": "doctor1@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )

        await test_db.doctors.insert_one(
            {
                "user_id": str(user1_result.inserted_id),
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [{"name": "Cardiology", "expertise_level": "expert"}],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": True,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )

        service = DoctorService()
        doctors = await service.search_doctors(specialization="Cardiology")

        assert len(doctors) > 0
        assert "Cardiology" in str(doctors[0]["specializations"])

    async def test_search_doctors_by_rating(self, test_db):
        """Test searching doctors by minimum rating."""
        # Create test users and doctors
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor1@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )

        await test_db.doctors.insert_one(
            {
                "user_id": str(user_result.inserted_id),
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": True,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )

        service = DoctorService()
        doctors = await service.search_doctors(rating_min=4.0)

        assert len(doctors) > 0
        assert doctors[0]["average_rating"] >= 4.0

    async def test_search_doctors_by_location(self, test_db):
        """Test searching doctors by location."""
        # Create test users and doctors
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor1@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )

        await test_db.doctors.insert_one(
            {
                "user_id": str(user_result.inserted_id),
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza, Boston, MA 02101",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": True,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )

        service = DoctorService()
        doctors = await service.search_doctors(location="Boston")

        assert len(doctors) > 0
        assert "Boston" in doctors[0]["clinic_address"]


class TestDoctorStatistics:
    """Test suite for doctor statistics."""

    async def test_get_doctor_statistics_success(self, test_db):
        """Test getting doctor statistics successfully."""
        # Create test user and doctor
        user_result = await test_db.users.insert_one(
            {
                "email": "doctor@example.com",
                "phone": "1234567890",
                "name": "Dr. John Smith",
                "role": "doctor",
                "is_active": True,
            }
        )
        user_id = str(user_result.inserted_id)

        doctor_result = await test_db.doctors.insert_one(
            {
                "user_id": user_id,
                "license_number": "DOC123456",
                "license_expiry": datetime.utcnow() + timedelta(days=365),
                "specializations": [{"name": "Cardiology", "expertise_level": "expert"}],
                "qualifications": [],
                "clinic_address": "123 Medical Plaza",
                "clinic_phone": "617-555-0123",
                "consultation_fee": 150.0,
                "working_hours": {},
                "is_verified": True,
                "average_rating": 4.5,
                "review_count": 10,
                "availability_status": "available",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }
        )
        doctor_id = str(doctor_result.inserted_id)

        # Create appointments
        await test_db.appointments.insert_many(
            [
                {
                    "doctor_id": doctor_id,
                    "patient_id": "patient1",
                    "date": datetime.utcnow(),
                    "start_time": "09:00",
                    "end_time": "09:30",
                    "status": "completed",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
                {
                    "doctor_id": doctor_id,
                    "patient_id": "patient2",
                    "date": datetime.utcnow(),
                    "start_time": "10:00",
                    "end_time": "10:30",
                    "status": "scheduled",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            ]
        )

        service = DoctorService()
        stats = await service.get_doctor_statistics(user_id)

        assert stats["total_appointments"] == 2
        assert stats["completed_appointments"] == 1
        assert stats["avg_rating"] == 4.5
        assert "Cardiology" in stats["specializations"]
