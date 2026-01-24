"""Consultation document-related data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Document type options."""

    xray = "xray"
    report = "report"
    lab = "lab"
    scan = "scan"
    other = "other"


class DocumentResponse(BaseModel):
    """Document response model."""

    document_id: str
    consultation_id: str
    document_url: str
    document_type: str
    file_name: str
    file_size: int
    uploaded_by: str
    uploader_name: Optional[str] = None
    description: Optional[str] = None
    is_scanned: bool = True
    created_at: datetime


class DocumentsListResponse(BaseModel):
    """Documents list response model."""

    documents: list[DocumentResponse]
    total_count: int
