"""Tests for database module."""
import pytest
from unittest.mock import Mock, AsyncMock


@pytest.mark.unit
def test_generate_id():
    """Test ID generation."""
    from app.database import generate_id

    id1 = generate_id("PT")
    id2 = generate_id("PT")

    assert id1 != id2
    assert id1.startswith("PT")
    assert len(id1) <= 32


@pytest.mark.unit
def test_generate_id_without_prefix():
    """Test ID generation without prefix."""
    from app.database import generate_id

    id1 = generate_id()
    id2 = generate_id()

    assert id1 != id2
    assert len(id1) <= 32


@pytest.mark.unit
def test_database_initialization():
    """Test Database class initialization."""
    from app.database import Database

    db = Database()
    assert db.client is None
    assert db.database is None


@pytest.mark.unit
def test_get_db_without_connection():
    """Test get_db raises error when not connected."""
    from app.database import Database

    db = Database()

    with pytest.raises(RuntimeError):
        db.get_db()


@pytest.mark.unit
async def test_ensure_indexes():
    """Test ensure_indexes creates indexes."""
    from app.database import ensure_indexes

    mock_db = Mock()
    mock_db.patients = Mock()
    mock_db.medical_history = Mock()
    mock_db.allergies = Mock()
    mock_db.insurance = Mock()
    mock_db.patients.create_index = AsyncMock()
    mock_db.medical_history.create_index = AsyncMock()
    mock_db.allergies.create_index = AsyncMock()
    mock_db.insurance.create_index = AsyncMock()

    await ensure_indexes(mock_db)

    mock_db.patients.create_index.assert_called()
    mock_db.medical_history.create_index.assert_called()
    mock_db.allergies.create_index.assert_called()
    mock_db.insurance.create_index.assert_called()
