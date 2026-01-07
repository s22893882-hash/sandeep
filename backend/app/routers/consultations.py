"""Consultation management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.auth import get_current_user, get_current_doctor_or_admin
from app.models.consultation import (
    ConsultationCreate,
    ConsultationResponse,
)
from app.services.consultation_service import ConsultationService
from app.database import get_database

router = APIRouter(prefix="/api/consultations", tags=["consultations"])


def get_consultation_service(db=Depends(get_database)) -> ConsultationService:
    """Get consultation service instance."""
    return ConsultationService(db)


@router.post("/start", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def start_consultation(
    data: ConsultationCreate,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Initialize consultation session."""
    return await service.start_consultation(data)


@router.get("/{id}", response_model=ConsultationResponse)
async def get_consultation(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Get consultation details."""
    try:
        return await service.get_consultation(id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/message", response_model=dict)
async def send_message(
    id: str,
    message: str,
    msg_type: str = "text",
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Send consultation message (chat)."""
    return await service.send_message(id, current_user["user_id"], message, msg_type)


@router.get("/{id}/messages", response_model=list)
async def get_messages(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Get consultation chat history."""
    return await service.get_messages(id)


@router.post("/{id}/prescription", response_model=dict)
async def add_prescription(
    id: str,
    patient_id: str,
    medications: List[dict],
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Doctor adds prescription."""
    return await service.add_prescription(id, current_user["user_id"], patient_id, medications)


@router.get("/{id}/prescriptions", response_model=list)
async def get_prescriptions(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Get prescriptions."""
    return await service.get_prescriptions(id)


@router.post("/{id}/notes", response_model=dict)
async def add_notes(
    id: str,
    notes: str,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Add clinical notes."""
    return await service.add_notes(id, current_user["user_id"], notes)


@router.get("/{id}/notes", response_model=list)
async def get_notes(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Get clinical notes."""
    return await service.get_notes(id)


@router.post("/{id}/attach-document", response_model=dict)
async def attach_document(
    id: str,
    document_url: str,
    file_type: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Attach medical documents/reports."""
    return await service.attach_document(id, document_url, file_type, current_user["user_id"])


@router.get("/{id}/documents", response_model=list)
async def get_documents(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Get attached documents."""
    return await service.get_documents(id)


@router.put("/{id}/close", response_model=dict)
async def close_consultation(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """End consultation."""
    try:
        return await service.close_consultation(id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/follow-up", response_model=dict)
async def follow_up(
    id: str,
    follow_up_date: str,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Schedule follow-up consultation."""
    return await service.schedule_follow_up(id, follow_up_date)


@router.get("/my-consultations", response_model=List[ConsultationResponse])
async def get_my_consultations(
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Retrieve patient's consultations."""
    return await service.get_patient_consultations(current_user["user_id"])


@router.get("/doctor-consultations", response_model=List[ConsultationResponse])
async def get_doctor_consultations(
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Retrieve doctor's consultations."""
    return await service.get_doctor_consultations(current_user["user_id"])


@router.post("/{id}/feedback", response_model=dict)
async def feedback(
    id: str,
    rating: int,
    comments: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Patient provides feedback."""
    return await service.provide_feedback(id, current_user["user_id"], rating, comments)


@router.get("/{id}/feedback", response_model=dict)
async def get_feedback(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Get consultation feedback."""
    feedback = await service.get_feedback(id)
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    # Convert _id if necessary, or just return as is if using Pydantic model with allowance for extra fields
    feedback["_id"] = str(feedback["_id"])
    return feedback


@router.post("/{id}/video-token", response_model=dict)
async def video_token(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Generate video call token."""
    return await service.generate_video_token(id)


@router.put("/{id}/status", response_model=dict)
async def update_status(
    id: str,
    status: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """Update consultation status."""
    return await service.update_status(id, status)
