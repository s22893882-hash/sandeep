"""Document service for managing consultation documents."""
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4
import mimetypes

from app.models.consultation_document import (
    DocumentType,
    DocumentResponse,
)


class DocumentService:
    """Service for handling document management."""

    ALLOWED_FILE_TYPES = {
        "application/pdf": "pdf",
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "application/msword": "doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "text/plain": "txt",
    }

    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes

    def __init__(self, db):
        """Initialize document service with database."""
        self.db = db

    async def generate_document_id(self) -> str:
        """Generate a unique document ID."""
        return f"DOC{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:6]}"

    async def validate_file_type(self, file_content_type: str) -> bool:
        """
        Validate file type.

        Args:
            file_content_type: The MIME type of the file

        Returns:
            True if valid, False otherwise
        """
        return file_content_type in self.ALLOWED_FILE_TYPES

    async def scan_file(self, file_content: bytes) -> bool:
        """
        Scan file for viruses.

        In production, this would integrate with a virus scanning service.
        For now, we'll mock the scan.

        Args:
            file_content: The file content

        Returns:
            True if clean, False if virus detected
        """
        # Mock virus scan - always returns clean
        # In production, integrate with ClamAV or similar
        return True

    async def encrypt_document(self, file_content: bytes) -> bytes:
        """
        Encrypt document at rest.

        In production, this would use proper encryption (e.g., AES-256).
        For now, we'll return the content as-is.

        Args:
            file_content: The file content

        Returns:
            Encrypted content
        """
        # Mock encryption - in production use proper encryption
        return file_content

    async def upload_document(
        self,
        consultation_id: str,
        user_id: str,
        file_name: str,
        file_content: bytes,
        file_size: int,
        document_type: DocumentType,
        description: str = None,
    ) -> DocumentResponse:
        """
        Upload a document to a consultation.

        Args:
            consultation_id: The consultation ID
            user_id: The user ID uploading the document
            file_name: The name of the file
            file_content: The file content
            file_size: The size of the file in bytes
            document_type: The type of document
            description: Optional description

        Returns:
            Created document response

        Raises:
            ValueError: If consultation not found, user not authorized, or file invalid
        """
        # Verify consultation exists
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if user_id not in [
            consultation["patient_id"],
            consultation["doctor_id"],
        ]:
            raise ValueError("Only consultation participants can upload documents")

        # Validate file size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum of {self.MAX_FILE_SIZE / (1024*1024)}MB")

        # Validate file type based on extension
        mime_type, _ = mimetypes.guess_type(file_name)
        if mime_type:
            is_valid = await self.validate_file_type(mime_type)
            if not is_valid:
                raise ValueError(f"File type {mime_type} is not allowed")

        # Virus scan
        is_clean = await self.scan_file(file_content)
        if not is_clean:
            raise ValueError("File failed virus scan")

        # Encrypt document
        encrypted_content = await self.encrypt_document(file_content)

        # Store document (in production, would use S3 or similar)
        # For now, we'll generate a mock URL
        document_id = await self.generate_document_id()
        document_url = f"https://secure-storage.com/{document_id}"
        created_at = datetime.utcnow()

        # Store metadata
        document_data = {
            "document_id": document_id,
            "consultation_id": consultation_id,
            "document_url": document_url,
            "document_type": document_type.value,
            "file_name": file_name,
            "file_size": file_size,
            "uploaded_by": user_id,
            "description": description,
            "is_scanned": True,
            "created_at": created_at,
        }

        await self.db.consultation_documents.insert_one(document_data)

        return DocumentResponse(
            document_id=document_id,
            consultation_id=consultation_id,
            document_url=document_url,
            document_type=document_type.value,
            file_name=file_name,
            file_size=file_size,
            uploaded_by=user_id,
            uploader_name=None,
            description=description,
            is_scanned=True,
            created_at=created_at,
        )

    async def get_documents(self, consultation_id: str) -> List[DocumentResponse]:
        """
        Get all documents for a consultation.

        Args:
            consultation_id: The consultation ID

        Returns:
            List of documents
        """
        cursor = self.db.consultation_documents.find(
            {"consultation_id": consultation_id}
        ).sort("created_at", -1)

        documents = []
        async for doc in cursor:
            documents.append(
                DocumentResponse(
                    document_id=doc["document_id"],
                    consultation_id=doc["consultation_id"],
                    document_url=doc["document_url"],
                    document_type=doc["document_type"],
                    file_name=doc["file_name"],
                    file_size=doc["file_size"],
                    uploaded_by=doc["uploaded_by"],
                    uploader_name=None,
                    description=doc.get("description"),
                    is_scanned=doc.get("is_scanned", False),
                    created_at=doc["created_at"],
                )
            )

        return documents

    async def get_document(
        self, document_id: str, consultation_id: str, user_id: str
    ) -> Dict[str, Any]:
        """
        Get a document by ID.

        Args:
            document_id: The document ID
            consultation_id: The consultation ID
            user_id: The user ID requesting the document

        Returns:
            Document data

        Raises:
            ValueError: If document not found or user not authorized
        """
        # Get document
        document = await self.db.consultation_documents.find_one(
            {"document_id": document_id, "consultation_id": consultation_id}
        )

        if not document:
            raise ValueError("Document not found")

        # Verify consultation and user authorization
        consultation = await self.db.consultations.find_one(
            {"consultation_id": consultation_id}
        )

        if not consultation:
            raise ValueError("Consultation not found")

        if user_id not in [
            consultation["patient_id"],
            consultation["doctor_id"],
        ]:
            raise ValueError("Not authorized to access this document")

        # Generate secure temporary URL for download
        # In production, this would be a signed S3 URL
        download_url = f"{document['document_url']}?token={uuid4().hex[:32]}"

        # Log access (audit trail)
        await self.db.document_access_logs.insert_one({
            "document_id": document_id,
            "consultation_id": consultation_id,
            "user_id": user_id,
            "accessed_at": datetime.utcnow(),
        })

        return {
            "document_id": document_id,
            "document_url": download_url,
            "file_name": document["file_name"],
            "file_size": document["file_size"],
            "content_type": mimetypes.guess_type(document["file_name"])[0],
        }
