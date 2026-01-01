"""Tests for main application."""
import pytest
from main import (
    get_app_version,
    health_check,
    calculate_sum,
    calculate_product,
    validate_email,
    User,
)


@pytest.mark.unit
def test_get_app_version():
    """Test app version retrieval."""
    version = get_app_version()
    assert version == "1.0.0"
    assert isinstance(version, str)


@pytest.mark.unit
def test_health_check():
    """Test health check endpoint."""
    result = health_check()
    assert result["status"] == "healthy"
    assert "version" in result
    assert result["version"] == "1.0.0"


@pytest.mark.unit
def test_calculate_sum():
    """Test sum calculation."""
    assert calculate_sum(2, 3) == 5
    assert calculate_sum(-1, 1) == 0
    assert calculate_sum(0, 0) == 0
    assert calculate_sum(100, 200) == 300


@pytest.mark.unit
def test_calculate_product():
    """Test product calculation."""
    assert calculate_product(2, 3) == 6
    assert calculate_product(-1, 1) == -1
    assert calculate_product(0, 5) == 0
    assert calculate_product(10, 10) == 100


@pytest.mark.unit
def test_validate_email():
    """Test email validation."""
    assert validate_email("test@example.com") is True
    assert validate_email("user@domain.co.uk") is True
    assert validate_email("invalid.email") is False
    assert validate_email("@example.com") is False
    assert validate_email("test@") is False


@pytest.mark.unit
def test_user_creation():
    """Test user creation."""
    user = User(1, "test@example.com", "testuser")
    assert user.id == 1
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.is_active is True


@pytest.mark.unit
def test_user_to_dict():
    """Test user to dictionary conversion."""
    user = User(1, "test@example.com", "testuser")
    user_dict = user.to_dict()
    
    assert user_dict["id"] == 1
    assert user_dict["email"] == "test@example.com"
    assert user_dict["username"] == "testuser"
    assert user_dict["is_active"] is True


@pytest.mark.unit
def test_user_deactivate():
    """Test user deactivation."""
    user = User(1, "test@example.com", "testuser")
    assert user.is_active is True
    
    user.deactivate()
    assert user.is_active is False


@pytest.mark.unit
def test_user_activate():
    """Test user activation."""
    user = User(1, "test@example.com", "testuser")
    user.deactivate()
    assert user.is_active is False
    
    user.activate()
    assert user.is_active is True


@pytest.mark.unit
def test_user_lifecycle():
    """Test complete user lifecycle."""
    user = User(1, "test@example.com", "testuser")
    
    # Initial state
    assert user.is_active is True
    
    # Deactivate
    user.deactivate()
    assert user.is_active is False
    
    # Reactivate
    user.activate()
    assert user.is_active is True
    
    # Check dictionary representation
    user_dict = user.to_dict()
    assert user_dict["is_active"] is True
