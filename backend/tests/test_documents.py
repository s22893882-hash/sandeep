"""Tests for document management."""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from bson import ObjectId
import io

from app.models.consultation_document import (
    DocumentType,
    DocumentResponse,
)
from app.services.document_service import DocumentService


@pytest.fixture
def mock_consultation():
    """Create a mock consultation."""
    return {
        "_id": ObjectId(),
        "consultation_id": "CON123",
        "appointment_id": "APT123",
        "patient_id": "patient123",
        "doctor_id": "doctor123",
        "status": "in-progress",
        "start_time": datetime.utcnow(),
        "end_time": None,
        "duration_minutes": None,
        "session_token": "token123",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_document():
    """Create a mock document."""
    return {
        "_id": ObjectId(),
        "document_id": "DOC123",
        "consultation_id": "CON123",
        "document_url": "https://secure-storage.com/DOC123",
        "document_type": "xray",
        "file_name": "chest_xray.pdf",
        "file_size": 2048000,
        "uploaded_by": "doctor123",
        "description": "Chest X-ray from 2025-01-15",
        "is_scanned": True,
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def document_service(db):
    """Create document service instance."""
    return DocumentService(db)


# Unit Tests for DocumentService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_document_success(document_service, db, mock_consultation):
    """Test uploading a document successfully."""
    await db.consultations.insert_one(mock_consultation)

    file_content = b"mock file content" * 100  # ~1.5KB
    file_name = "test_report.pdf"

    document = await document_service.upload_document(
        consultation_id="CON123",
        user_id="doctor123",
        file_name=file_name,
        file_content=file_content,
        file_size=len(file_content),
        document_type=DocumentType.report,
        description="Test document",
    )

    assert document.consultation_id == "CON123"
    assert document.file_name == file_name
    assert document.document_type == "report"
    assert document.uploaded_by == "doctor123"
    assert document.description == "Test document"
    assert document.is_scanned is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_document_unauthorized(document_service, db, mock_consultation):
    """Test uploading document without authorization."""
    await db.consultations.insert_one(mock_consultation)

    with pytest.raises(ValueError, match="Only consultation participants"):
        await document_service.upload_document(
            consultation_id="CON123",
            user_id="unauthorized_user",
            file_name="test.pdf",
            file_content=b"content",
            file_size=100,
            document_type=DocumentType.report,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_document_too_large(document_service, db, mock_consultation):
    """Test uploading a file that's too large."""
    await db.consultations.insert_one(mock_consultation)

    # Create a file larger than 100MB
    file_content = b"x" * (101 * 1024 * 1024)

    with pytest.raises(ValueError, match="File size exceeds maximum"):
        await document_service.upload_document(
            consultation_id="CON123",
            user_id="doctor123",
            file_name="large.pdf",
            file_content=file_content,
            file_size=len(file_content),
            document_type=DocumentType.report,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_document_invalid_type(document_service, db, mock_consultation):
    """Test uploading a file with invalid type."""
    await db.consultations.insert_one(mock_consultation)

    with pytest.raises(ValueError, match="File type.*is not allowed"):
        await document_service.upload_document(
            consultation_id="CON123",
            user_id="doctor123",
            file_name="test.exe",  # .exe files are not allowed
            file_content=b"content",
            file_size=100,
            document_type=DocumentType.report,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_documents(document_service, db, mock_consultation, mock_document):
    """Test getting documents for a consultation."""
    await db.consultations.insert_one(mock_consultation)
    await db.consultation_documents.insert_one(mock_document)

    documents = await document_service.get_documents("CON123")

    assert len(documents) >= 1
    assert documents[0].document_id == "DOC123"
    assert documents[0].file_name == "chest_xray.pdf"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_documents_empty(document_service, db, mock_consultation):
    """Test getting documents when none exist."""
    await db.consultations.insert_one(mock_consultation)

    documents = await document_service.get_documents("CON123")

    assert len(documents) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_document(document_service, db, mock_consultation, mock_document):
    """Test getting a specific document."""
    await db.consultations.insert_one(mock_consultation)
    await db.consultation_documents.insert_one(mock_document)

    document = await document_service.get_document(
        "DOC123", "CON123", "doctor123"
    )

    assert document["document_id"] == "DOC123"
    assert document["file_name"] == "chest_xray.pdf"
    assert "document_url" in document


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_document_not_found(document_service, db, mock_consultation):
    """Test getting a non-existent document."""
    await db.consultations.insert_one(mock_consultation)

    with pytest.raises(ValueError, match="Document not found"):
        await document_service.get_document(
            "NONEXISTENT", "CON123", "doctor123"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_document_unauthorized(document_service, db, mock_consultation, mock_document):
    """Test getting a document without authorization."""
    await db.consultations.insert_one(mock_consultation)
    await db.consultation_documents.insert_one(mock_document)

    with pytest.raises(ValueError, match="Not authorized"):
        await document_service.get_document(
            "DOC123", "CON123", "unauthorized_user"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_file_type(document_service):
    """Test file type validation."""
    # Valid types
    assert await document_service.validate_file_type("application/pdf") is True
    assert await document_service.validate_file_type("image/jpeg") is True
    assert await document_service.validate_file_type("image/png") is True

    # Invalid types
    assert await document_service.validate_file_type("application/exe") is False
    assert await document_service.validate_file_type("application/zip") is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scan_file(document_service):
    """Test virus scanning (mock)."""
    file_content = b"safe file content"

    is_clean = await document_service.scan_file(file_content)

    assert is_clean is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_encrypt_document(document_service):
    """Test document encryption (mock)."""
    file_content = b"original content"

    encrypted = await document_service.encrypt_document(file_content)

    assert encrypted is not None


# Endpoint Tests


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_document_endpoint(client, db, auth_headers, mock_consultation):
    """Test uploading document via API endpoint."""
    await db.consultations.insert_one(mock_consultation)

    # Create a mock file
    file_content = b"mock pdf content" * 100
    files = {"file": ("test_report.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {
        "document_type": "report",
        "description": "Test report",
    }

    response = await client.post(
        "/api/consultations/CON123/attach-document",
        files=files,
        data=data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["consultation_id"] == "CON123"
    assert data["file_name"] == "test_report.pdf"
    assert data["document_type"] == "report"
    assert data["is_scanned"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_documents_endpoint(client, db, auth_headers, mock_consultation, mock_document):
    """Test getting documents via API endpoint."""
    await db.consultations.insert_one(mock_consultation)
    await db.consultation_documents.insert_one(mock_document)

    response = await client.get(
        "/api/consultations/CON123/documents",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert data["total_count"] >= 1
    assert len(data["documents"]) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_image_document(client, db, auth_headers, mock_consultation):
    """Test uploading an image document."""
    await db.consultations.insert_one(mock_consultation)

    file_content = b"mock image content"
    files = {"file": ("xray.jpg", io.BytesIO(file_content), "image/jpeg")}
    data = {
        "document_type": "xray",
        "description": "Chest X-ray",
    }

    response = await client.post(
        "/api/consultations/CON123/attach-document",
        files=files,
        data=data,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["document_type"] == "xray"
    assert data["file_name"] == "xray.jpg"
