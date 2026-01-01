"""Test configuration and fixtures for doctor management system."""

import pytest
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Database
from app.core.config import settings


@pytest.fixture(scope="session")
async def test_db():
    """Create test database connection for the entire test session."""
    original_db = settings.MONGODB_DATABASE
    settings.MONGODB_DATABASE = "doctor_management_test"

    # Use in-memory MongoDB for testing or create test specific database
    if not Database.client:
        try:
            import motor

            Database.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
            Database.db = Database.client[settings.MONGODB_DATABASE]

            # Create test indexes
            await Database.create_indexes()
        except Exception:
            pytest.skip("MongoDB not available for testing")

    yield Database.db

    # Cleanup after all tests
    if Database.client:
        await Database.client.drop_database(settings.MONGODB_DATABASE)
    settings.MONGODB_DATABASE = original_db


@pytest.fixture(autouse=True)
async def cleanup_db(test_db):
    """Clean up database between tests."""
    collections = await test_db.list_collection_names()
    for collection in collections:
        if not collection.startswith("system."):
            await test_db[collection].delete_many({})
    yield


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {"email": "test@example.com", "phone": "1234567890", "name": "Test User", "role": "doctor", "is_active": True}


@pytest.fixture
def test_doctor_data():
    """Sample doctor data for testing."""
    return {
        "license_number": "DOC123456",
        "license_expiry": datetime.utcnow(),
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
        "bio": "Test bio",
        "languages": ["English"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
    }


@pytest.fixture
def sample_registration_data():
    """Sample doctor registration request data."""
    from datetime import datetime, timedelta
    from app.schemas.doctors import DoctorRegistrationRequest

    return DoctorRegistrationRequest(
        license_number="DOC123456",
        license_expiry=datetime.utcnow() + timedelta(days=365),
        specialization=[{"specialization_name": "Cardiology", "expertise_level": "expert"}],
        qualifications=[{"degree": "MD", "institution": "Harvard Medical School", "year": 2010, "field": "Cardiology"}],
        clinic_address="123 Medical Plaza, Boston, MA 02101",
        clinic_phone="617-555-0123",
        consultation_fee=150.0,
        working_hours={
            "Monday": {"start": "09:00", "end": "17:00"},
            "Tuesday": {"start": "09:00", "end": "17:00"},
            "Wednesday": {"start": "09:00", "end": "17:00"},
            "Thursday": {"start": "09:00", "end": "17:00"},
            "Friday": {"start": "09:00", "end": "17:00"},
        },
        bio="Experienced cardiologist",
        languages=["English", "Spanish"],
        license_document_url="https://example.com/license.pdf",
    )


@pytest.fixture
def mock_jwt_token():
    """Valid JWT token for testing."""
    from app.core.security import create_access_token

    return create_access_token(data={"sub": "test_user_id", "email": "doctor@example.com", "role": "doctor"})


@pytest.fixture
def mock_doctor_jwt_token():
    """Valid doctor JWT token for testing."""
    from app.core.security import create_access_token
    from bson import ObjectId

    return create_access_token(data={"sub": str(ObjectId()), "email": "doctor@example.com", "role": "doctor"})


@pytest.fixture
def mock_admin_jwt_token():
    """Valid admin JWT token for testing."""
    from app.core.security import create_access_token

    return create_access_token(data={"sub": "admin_user_id", "email": "admin@doctorapp.com", "role": "admin"})
