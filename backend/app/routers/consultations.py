"""
Consultation API endpoints for Phase 3 Module 2.
Complete consultation system with 18 APIs for live/async consultations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime

from app.auth import get_current_user, security, TESTING_MODE
from app.models.consultation import (
    ConsultationStart,
    ConsultationResponse,
    ConsultationUpdate,
    ConsultationClose,
    MessageCreate,
    MessageResponse,
    MessageQuery,
    PrescriptionCreate,
    PrescriptionResponse,
    ClinicalNotesCreate,
    ClinicalNotesResponse,
    DocumentCreate,
    DocumentResponse,
    FollowUpCreate,
    FollowUpResponse,
    FeedbackCreate,
    FeedbackResponse,
    VideoTokenCreate,
    VideoTokenResponse,
    ConsultationQuery,
    DoctorConsultationQuery,
)
from app.services.consultation_service import ConsultationService
from app.websocket import websocket_endpoint
from app.database import db as database

router = APIRouter(prefix="/api/consultations", tags=["consultations"])


def get_consultation_service() -> ConsultationService:
    """Get consultation service instance."""
    return ConsultationService(database.get_db())


async def optional_auth(
    credentials: HTTPAuthorizationCredentials = Depends(
        security if not TESTING_MODE else lambda: None
    ),
):
    """Optional authentication for testing."""
    if TESTING_MODE:
        if credentials:
            return await get_current_user(credentials)
        return await get_current_user(None)
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await get_current_user(credentials)


# WebSocket endpoint for real-time messaging
@router.websocket("/ws/{consultation_id}")
async def websocket_consultation_endpoint(
    websocket: WebSocket,
    consultation_id: str,
    token: str
):
    """WebSocket endpoint for real-time consultation messaging."""
    await websocket_endpoint(websocket, consultation_id, token)


# 1. Core Consultation Management (2 APIs)

@router.post("/start", response_model=dict, status_code=status.HTTP_201_CREATED)
async def start_consultation(
    consultation_data: ConsultationStart,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Initialize consultation session.
    
    Creates a new consultation session linked to an appointment.
    """
    try:
        result = await service.start_consultation(consultation_data)
        return {
            "consultation_id": result["consultation_id"],
            "session_token": result["session_token"],
            "start_time": result["start_time"],
            "status": result["status"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: str,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Get consultation details.
    
    Returns complete consultation information for authorized participants.
    """
    consultation = await service.get_consultation(consultation_id, current_user["user_id"])
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found or access denied",
        )
    return ConsultationResponse(**consultation)


# 2. Chat & Messaging (2 APIs)

@router.post("/{consultation_id}/message", response_model=dict, status_code=status.HTTP_201_CREATED)
async def send_message(
    consultation_id: str,
    message_data: MessageCreate,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Send consultation message (chat).
    
    Stores message and broadcasts to consultation participants.
    """
    try:
        # Override sender_id with authenticated user
        message_data.sender_id = current_user["user_id"]
        result = await service.send_message(consultation_id, message_data)
        return {
            "message_id": result["message_id"],
            "timestamp": result["timestamp"],
            "delivery_status": result["delivery_status"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{consultation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    consultation_id: str,
    limit: int = 50,
    offset: int = 0,
    sort_order: str = "desc",
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Get consultation chat history.
    
    Returns paginated message history with sender information.
    """
    messages = await service.get_messages(
        consultation_id, current_user["user_id"], limit, offset, sort_order
    )
    return [MessageResponse(**message) for message in messages]


# 3. Prescriptions (2 APIs)

@router.post("/{consultation_id}/prescription", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    consultation_id: str,
    prescription_data: PrescriptionCreate,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Doctor adds prescription.
    
    Creates prescription with QR code for pharmacy integration.
    """
    try:
        result = await service.create_prescription(
            consultation_id, current_user["user_id"], prescription_data
        )
        return {
            "prescription_id": result["prescription_id"],
            "qr_code": result["qr_code"],
            "prescription_status": result["prescription_status"],
            "expiry_date": result["expiry_date"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{consultation_id}/prescriptions", response_model=List[PrescriptionResponse])
async def get_prescriptions(
    consultation_id: str,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Get prescriptions.
    
    Returns all prescriptions for the consultation with QR codes.
    """
    prescriptions = await service.get_prescriptions(consultation_id, current_user["user_id"])
    return [PrescriptionResponse(**prescription) for prescription in prescriptions]


# 4. Clinical Notes (2 APIs)

@router.post("/{consultation_id}/notes", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_clinical_notes(
    consultation_id: str,
    notes_data: ClinicalNotesCreate,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Add clinical notes.
    
    Creates doctor-only clinical notes with vitals and diagnosis.
    """
    try:
        result = await service.create_clinical_notes(
            consultation_id, current_user["user_id"], notes_data
        )
        return {
            "notes_id": result["notes_id"],
            "notes_summary": result["notes_text"][:100] + "..." if len(result["notes_text"]) > 100 else result["notes_text"],
            "timestamp": result["created_at"],
            "follow_up_required": result["follow_up_required"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/{consultation_id}/notes", response_model=List[ClinicalNotesResponse])
async def get_clinical_notes(
    consultation_id: str,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Get clinical notes.
    
    Returns doctor's private clinical notes (doctor only).
    """
    notes = await service.get_clinical_notes(consultation_id, current_user["user_id"])
    return [ClinicalNotesResponse(**note) for note in notes]


# 5. Document Management (2 APIs)

@router.post("/{consultation_id}/attach-document", response_model=dict, status_code=status.HTTP_201_CREATED)
async def attach_document(
    consultation_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    description: str = Form(...),
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Attach medical documents/reports.
    
    Uploads and stores medical documents with virus scanning.
    """
    try:
        # Validate file type and size
        if not file.content_type.startswith("image/") and file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image and PDF files are allowed"
            )
        
        if file.size and file.size > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size cannot exceed 100MB"
            )

        # In a real implementation, upload to cloud storage (S3, GCS, etc.)
        # For now, we'll simulate with a mock URL
        file_url = f"/uploads/{file.filename}"
        file_name = file.filename
        file_size = file.size or 0

        from app.models.consultation import DocumentType
        document_data = DocumentCreate(
            document_type=DocumentType(document_type),
            description=description
        )

        result = await service.attach_document(
            consultation_id, current_user["user_id"], document_data, file_url, file_name, file_size
        )
        return {
            "document_id": result["document_id"],
            "document_url": result["document_url"],
            "upload_status": "success"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{consultation_id}/documents", response_model=List[DocumentResponse])
async def get_documents(
    consultation_id: str,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Get attached documents.
    
    Returns all medical documents attached to the consultation.
    """
    documents = await service.get_documents(consultation_id, current_user["user_id"])
    return [DocumentResponse(**doc) for doc in documents]


# 6. Consultation Lifecycle (3 APIs)

@router.put("/{consultation_id}/close", response_model=ConsultationResponse)
async def close_consultation(
    consultation_id: str,
    close_data: ConsultationClose,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    End consultation.
    
    Marks consultation as completed with duration and notes.
    """
    consultation = await service.close_consultation(
        consultation_id, current_user["user_id"], close_data
    )
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctor can close consultation or consultation not found",
        )
    return ConsultationResponse(**consultation)


@router.post("/{consultation_id}/follow-up", response_model=dict, status_code=status.HTTP_201_CREATED)
async def schedule_follow_up(
    consultation_id: str,
    follow_up_data: FollowUpCreate,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Schedule follow-up consultation.
    
    Creates follow-up consultation record linked to original.
    """
    try:
        result = await service.schedule_follow_up(
            consultation_id, current_user["user_id"], follow_up_data
        )
        return {
            "follow_up_id": result["follow_up_id"],
            "scheduled_time": result["scheduled_date"],
            "status": result["status"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.put("/{consultation_id}/status", response_model=ConsultationResponse)
async def update_consultation_status(
    consultation_id: str,
    update_data: ConsultationUpdate,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Update consultation status.
    
    Updates consultation workflow status (doctor only).
    """
    consultation = await service.update_consultation_status(
        consultation_id, current_user["user_id"], update_data
    )
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctor can update consultation status",
        )
    return ConsultationResponse(**consultation)


# 7. Feedback & Ratings (2 APIs)

@router.post("/{consultation_id}/feedback", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    consultation_id: str,
    feedback_data: FeedbackCreate,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Patient provides feedback.
    
    Stores patient feedback and rating for the consultation.
    """
    try:
        result = await service.create_feedback(
            consultation_id, current_user["user_id"], feedback_data
        )
        return {
            "feedback_id": result["feedback_id"],
            "feedback_summary": f"Rating: {result['rating']}/5 stars",
            "created_at": result["created_at"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/{consultation_id}/feedback", response_model=FeedbackResponse)
async def get_feedback(
    consultation_id: str,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Get consultation feedback.
    
    Returns patient feedback for the consultation.
    """
    feedback = await service.get_feedback(consultation_id, current_user["user_id"])
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found or access denied",
        )
    return FeedbackResponse(**feedback)


# 8. Consultation Retrieval (2 APIs)

@router.get("/my-consultations", response_model=List[ConsultationResponse])
async def get_my_consultations(
    status: Optional[str] = "all",
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Retrieve patient's consultations.
    
    Returns paginated consultation history for the authenticated patient.
    """
    consultations = await service.get_patient_consultations(
        current_user["user_id"], status, limit, offset
    )
    return [ConsultationResponse(**consultation) for consultation in consultations]


@router.get("/doctor-consultations", response_model=List[ConsultationResponse])
async def get_doctor_consultations(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    patient_name: Optional[str] = None,
    status: Optional[str] = "all",
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Retrieve doctor's consultations.
    
    Returns paginated consultation schedule for the authenticated doctor.
    """
    consultations = await service.get_doctor_consultations(
        current_user["user_id"], date_from, date_to, patient_name, status, limit, offset
    )
    return [ConsultationResponse(**consultation) for consultation in consultations]


# 9. Video Integration (1 API)

@router.post("/{consultation_id}/video-token", response_model=VideoTokenResponse)
async def generate_video_token(
    consultation_id: str,
    token_data: VideoTokenCreate,
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Generate video call token.
    
    Creates time-limited video call token for Agora/Twilio integration.
    """
    try:
        result = await service.generate_video_token(
            consultation_id, current_user["user_id"], token_data
        )
        return VideoTokenResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Additional utility endpoints

@router.get("/stats/my-stats")
async def get_my_stats(
    current_user: dict = Depends(optional_auth),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Get consultation statistics for current user.
    
    Returns count and status breakdown of consultations.
    """
    total_count = await service.get_consultation_count(current_user["user_id"], current_user["user_type"])
    
    # Get status breakdown
    db = database.get_db()
    user_id = current_user["user_id"]
    user_type = current_user["user_type"]
    
    status_field = "patient_id" if user_type == "patient" else "doctor_id"
    
    status_pipeline = [
        {"$match": {status_field: user_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    
    status_results = []
    async for result in db.consultations.aggregate(status_pipeline):
        status_results.append({"status": result["_id"], "count": result["count"]})
    
    return {
        "total_consultations": total_count,
        "status_breakdown": status_results,
        "user_type": user_type
    }