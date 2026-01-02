"""Tests for auth module."""
import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

os.environ["ENVIRONMENT"] = "test"


@pytest.fixture
def test_user_payload():
    """Test user payload."""
    return {
        "sub": "user123",
        "email": "test@example.com",
        "role": "patient",
    }


# Unit tests for auth module


@pytest.mark.unit
def test_create_access_token(test_user_payload):
    """Test JWT token creation."""
    from app.auth import create_access_token, SECRET_KEY, ALGORITHM

    token = create_access_token(test_user_payload)

    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.unit
def test_create_access_token_with_expiry(test_user_payload):
    """Test JWT token creation with custom expiry."""
    from app.auth import create_access_token

    expires_delta = timedelta(minutes=60)
    token = create_access_token(test_user_payload, expires_delta)

    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.unit
def test_decode_token_valid(test_user_payload):
    """Test JWT token decoding with valid token."""
    from app.auth import create_access_token, decode_token

    token = create_access_token(test_user_payload)
    decoded = decode_token(token)

    assert decoded["sub"] == "user123"
    assert decoded["email"] == "test@example.com"
    assert decoded["role"] == "patient"
    assert "exp" in decoded


@pytest.mark.unit
def test_decode_token_invalid():
    """Test JWT token decoding with invalid token."""
    from app.auth import decode_token
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        decode_token("invalid.token.here")

    assert exc_info.value.status_code == 401


@pytest.mark.unit
async def test_get_current_user_in_test_mode():
    """Test get_current_user in test mode."""
    from app.auth import get_current_user

    # In test mode with no credentials, should return default test user
    user = await get_current_user(None)

    assert user["user_id"] == "test_user_id"
    assert user["email"] == "test@example.com"
    assert user["role"] == "patient"


@pytest.mark.unit
async def test_get_current_user_with_fake_token():
    """Test get_current_user with fake token in test mode."""
    from app.auth import get_current_user
    from unittest.mock import Mock
    from fastapi.security import HTTPAuthorizationCredentials

    credentials = Mock(spec=HTTPAuthorizationCredentials)
    credentials.credentials = "fake_token"

    user = await get_current_user(credentials)

    assert user["user_id"] == "user123"
    assert user["email"] == "test@example.com"


@pytest.mark.unit
async def test_get_current_user_no_credentials():
    """Test get_current_user with no credentials raises error."""
    from app.auth import get_current_user, TESTING_MODE

    # Temporarily disable test mode
    import app.auth as auth_module
    original_mode = auth_module.TESTING_MODE
    auth_module.TESTING_MODE = False

    try:
        with pytest.raises(Exception):
            await get_current_user(None)
    finally:
        auth_module.TESTING_MODE = original_mode


@pytest.mark.unit
async def test_get_current_patient_allowed():
    """Test get_current_patient allows patient role."""
    from app.auth import get_current_patient

    patient_user = {"user_id": "user123", "email": "test@example.com", "role": "patient"}
    result = await get_current_patient(patient_user)

    assert result == patient_user


@pytest.mark.unit
async def test_get_current_patient_with_admin():
    """Test get_current_patient allows admin role."""
    from app.auth import get_current_patient

    admin_user = {"user_id": "admin123", "email": "admin@example.com", "role": "admin"}
    result = await get_current_patient(admin_user)

    assert result == admin_user


@pytest.mark.unit
async def test_get_current_patient_denied_for_doctor():
    """Test get_current_patient denies doctor role."""
    from app.auth import get_current_patient
    from fastapi import HTTPException

    doctor_user = {"user_id": "doctor123", "email": "doctor@example.com", "role": "doctor"}

    with pytest.raises(HTTPException) as exc_info:
        await get_current_patient(doctor_user)

    assert exc_info.value.status_code == 403
    assert "Only patients can access" in exc_info.value.detail


@pytest.mark.unit
async def test_get_current_doctor_or_admin_allowed_for_doctor():
    """Test get_current_doctor_or_admin allows doctor."""
    from app.auth import get_current_doctor_or_admin

    doctor_user = {"user_id": "doctor123", "email": "doctor@example.com", "role": "doctor"}
    result = await get_current_doctor_or_admin(doctor_user)

    assert result == doctor_user


@pytest.mark.unit
async def test_get_current_doctor_or_admin_allowed_for_admin():
    """Test get_current_doctor_or_admin allows admin."""
    from app.auth import get_current_doctor_or_admin

    admin_user = {"user_id": "admin123", "email": "admin@example.com", "role": "admin"}
    result = await get_current_doctor_or_admin(admin_user)

    assert result == admin_user


@pytest.mark.unit
async def test_get_current_doctor_or_admin_denied_for_patient():
    """Test get_current_doctor_or_admin denies patient."""
    from app.auth import get_current_doctor_or_admin
    from fastapi import HTTPException

    patient_user = {"user_id": "user123", "email": "test@example.com", "role": "patient"}

    with pytest.raises(HTTPException) as exc_info:
        await get_current_doctor_or_admin(patient_user)

    assert exc_info.value.status_code == 403
    assert "Only doctors or admins" in exc_info.value.detail


@pytest.mark.unit
async def test_get_current_admin_allowed():
    """Test get_current_admin allows admin."""
    from app.auth import get_current_admin

    admin_user = {"user_id": "admin123", "email": "admin@example.com", "role": "admin"}
    result = await get_current_admin(admin_user)

    assert result == admin_user


@pytest.mark.unit
async def test_get_current_admin_denied_for_patient():
    """Test get_current_admin denies patient."""
    from app.auth import get_current_admin
    from fastapi import HTTPException

    patient_user = {"user_id": "user123", "email": "test@example.com", "role": "patient"}

    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin(patient_user)

    assert exc_info.value.status_code == 403
    assert "Only admins" in exc_info.value.detail


@pytest.mark.unit
async def test_get_current_admin_denied_for_doctor():
    """Test get_current_admin denies doctor."""
    from app.auth import get_current_admin
    from fastapi import HTTPException

    doctor_user = {"user_id": "doctor123", "email": "doctor@example.com", "role": "doctor"}

    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin(doctor_user)

    assert exc_info.value.status_code == 403
    assert "Only admins" in exc_info.value.detail


@pytest.mark.unit
def test_testing_mode_is_set():
    """Test that TESTING_MODE is set correctly."""
    from app.auth import TESTING_MODE

    assert TESTING_MODE is True
