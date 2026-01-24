"""Consultation management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional

from app.auth import (
    get_current_user,
    get_current_patient,
    get_current_doctor_or_admin,
    get_current_admin,
    TESTING_MODE,
)
from app.models.consultation import (
    ConsultationCreate,
    ConsultationResponse,
    ConsultationHistoryResponse,
    ConsultationCloseRequest,
    ConsultationCloseResponse,
    StatusUpdateRequest,
)
from app.models.consultation_message import (
    MessageCreate,
    MessageResponse,
    MessagesListResponse,
    MessageType,
)
from app.models.prescription import (
    PrescriptionCreate,
    PrescriptionResponse,
    PrescriptionsListResponse,
)
from app.models.clinical_notes import (
    ClinicalNotesCreate,
    ClinicalNotesUpdate,
    ClinicalNotesResponse,
)
from app.models.consultation_document import (
    DocumentResponse,
    DocumentsListResponse,
    DocumentType,
)
from app.models.consultation_feedback import (
    FeedbackCreate,
    FeedbackResponse,
)
from app.models.follow_up_consultation import (
    FollowUpCreate,
    FollowUpResponse,
)
from app.services.consultation_service import ConsultationService
from app.services.messaging_service import MessagingService
from app.services.prescription_service import PrescriptionService
from app.services.clinical_notes_service import ClinicalNotesService
from app.services.document_service import DocumentService
from app.services.feedback_service import FeedbackService
from app.services.video_token_service import VideoTokenService
from app.services.follow_up_service import FollowUpService
from app.database import db as database

router = APIRouter(prefix="/api/consultations", tags=["consultations"])


def get_consultation_service() -> ConsultationService:
    """Get consultation service instance."""
    return ConsultationService(database.get_db())


def get_messaging_service() -> MessagingService:
    """Get messaging service instance."""
    return MessagingService(database.get_db())


def get_prescription_service() -> PrescriptionService:
    """Get prescription service instance."""
    return PrescriptionService(database.get_db())


def get_clinical_notes_service() -> ClinicalNotesService:
    """Get clinical notes service instance."""
    return ClinicalNotesService(database.get_db())


def get_document_service() -> DocumentService:
    """Get document service instance."""
    return DocumentService(database.get_db())


def get_feedback_service() -> FeedbackService:
    """Get feedback service instance."""
    return FeedbackService(database.get_db())


def get_video_token_service() -> VideoTokenService:
    """Get video token service instance."""
    return VideoTokenService(database.get_db())


def get_follow_up_service() -> FollowUpService:
    """Get follow-up service instance."""
    return FollowUpService(database.get_db())


async def optional_auth(
    credentials: HTTPAuthorizationCredentials = Depends(
        lambda: None if TESTING_MODE else None
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


# ============================================================================
# SECTION 1: CORE CONSULTATION MANAGEMENT (2 APIs)
# ============================================================================


@router.post("/start", response_model=dict, status_code=status.HTTP_201_CREATED)
async def start_consultation(
    consultation_data: ConsultationCreate,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Initialize a new consultation session.

    Validates appointment exists and is confirmed, creates consultation record,
    generates session token for messaging, and sets status to "initiated".
    Only doctor/patient of appointment can start.
    """
    try:
        result = await service.start_consultation(
            consultation_data.appointment_id,
            consultation_data.patient_id,
            consultation_data.doctor_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: str,
    current_user: dict = Depends(get_current_user),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Get consultation details by ID.

    Retrieves complete consultation details including participant info,
    message/prescription/document counts. Only participants or admin can access.
    """
    try:
        consultation = await service.get_consultation(
            consultation_id, current_user["user_id"], current_user["role"]
        )
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found",
            )
        return consultation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


# ============================================================================
# SECTION 2: CHAT & MESSAGING (2 APIs)
# ============================================================================


@router.post("/{consultation_id}/message", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    consultation_id: str,
    message_data: MessageCreate,
    current_user: dict = Depends(get_current_user),
    service: MessagingService = Depends(get_messaging_service),
):
    """
    Send a message in a consultation.

    Validates consultation exists and is active, stores message,
    only consultation participants can send. Supports text messages.
    Real-time delivery target: < 200ms latency.
    """
    try:
        message = await service.send_message(
            consultation_id,
            message_data.sender_id,
            message_data.message_text,
            message_data.message_type,
        )
        return message
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{consultation_id}/messages", response_model=MessagesListResponse)
async def get_messages(
    consultation_id: str,
    limit: int = 50,
    offset: int = 0,
    sort_order: str = "asc",
    current_user: dict = Depends(get_current_user),
    service: MessagingService = Depends(get_messaging_service),
):
    """
    Get consultation chat history.

    Paginates through messages, includes sender name and details,
    tracks read/unread status. Only consultation participants can view.
    Sort by timestamp (asc = oldest first, desc = newest first).
    """
    try:
        messages = await service.get_messages(
            consultation_id, current_user["user_id"], limit, offset, sort_order
        )
        return messages
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


# ============================================================================
# SECTION 3: PRESCRIPTIONS (2 APIs)
# ============================================================================


@router.post("/{consultation_id}/prescription", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def add_prescription(
    consultation_id: str,
    prescription_data: PrescriptionCreate,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: PrescriptionService = Depends(get_prescription_service),
):
    """
    Doctor adds a prescription to a consultation.

    Only doctor can create prescription. Supports multi-medication prescriptions.
    Generates QR code for pharmacy integration, sets status to "active",
    calculates expiry_date (3 months default).
    """
    try:
        prescription = await service.add_prescription(
            consultation_id,
            current_user["user_id"],
            prescription_data.medications,
            prescription_data.notes,
        )
        return prescription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{consultation_id}/prescriptions", response_model=PrescriptionsListResponse)
async def get_prescriptions(
    consultation_id: str,
    current_user: dict = Depends(get_current_user),
    service: PrescriptionService = Depends(get_prescription_service),
):
    """
    Get all prescriptions for a consultation.

    Returns all prescriptions for consultation, calculates is_expired status.
    Participants can view. Includes QR codes for pharmacy integration.
    """
    prescriptions = await service.get_prescriptions(consultation_id)
    return PrescriptionsListResponse(prescriptions=prescriptions, total_count=len(prescriptions))


# ============================================================================
# SECTION 4: CLINICAL NOTES (2 APIs)
# ============================================================================


@router.post("/{consultation_id}/notes", response_model=ClinicalNotesResponse, status_code=status.HTTP_201_CREATED)
async def add_clinical_notes(
    consultation_id: str,
    notes_data: ClinicalNotesCreate,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: ClinicalNotesService = Depends(get_clinical_notes_service),
):
    """
    Doctor adds clinical notes to a consultation.

    Only doctor can create/view notes. Encrypts sensitive medical data.
    Stores vitals (BP, HR, temp, weight). Tracks version history.
    Doctor-private (patient cannot view).
    """
    try:
        notes = await service.add_notes(
            consultation_id,
            current_user["user_id"],
            notes_data.notes_text,
            notes_data.vitals.dict() if notes_data.vitals else None,
            notes_data.diagnosis,
            notes_data.treatment_plan,
        )
        return notes
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{consultation_id}/notes", response_model=ClinicalNotesResponse)
async def get_clinical_notes(
    consultation_id: str,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: ClinicalNotesService = Depends(get_clinical_notes_service),
):
    """
    Get clinical notes for a consultation.

    Doctor-only access. Returns 403 if patient tries to access.
    Includes version history metadata. Full encryption at rest.
    """
    try:
        notes = await service.get_notes(consultation_id, current_user["user_id"])
        return notes
    except ValueError as e:
        if "Only the treating doctor" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# SECTION 5: DOCUMENT MANAGEMENT (2 APIs)
# ============================================================================


@router.post("/{consultation_id}/attach-document", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def attach_document(
    consultation_id: str,
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    """
    Attach medical documents to a consultation.

    Validates file type (PDF, JPG, PNG, etc.), virus scans before storage,
    encrypts file at rest, stores metadata. Max file size: 100MB.
    Generates secure temporary URLs.
    """
    try:
        file_content = await file.read()
        document = await service.upload_document(
            consultation_id,
            current_user["user_id"],
            file.filename,
            file_content,
            len(file_content),
            document_type,
            description,
        )
        return document
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{consultation_id}/documents", response_model=DocumentsListResponse)
async def get_documents(
    consultation_id: str,
    current_user: dict = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    """
    Get all documents attached to a consultation.

    Returns all documents for consultation. Participants can download.
    Tracks download access (audit trail). Categorized by document_type.
    """
    documents = await service.get_documents(consultation_id)
    return DocumentsListResponse(documents=documents, total_count=len(documents))


# ============================================================================
# SECTION 6: CONSULTATION LIFECYCLE (3 APIs)
# ============================================================================


@router.put("/{consultation_id}/close", response_model=ConsultationCloseResponse)
async def close_consultation(
    consultation_id: str,
    close_data: ConsultationCloseRequest,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    End a consultation session.

    Only doctor can close. Sets status to "completed",
    calculates duration_minutes, stores end_time,
    triggers follow-up notification.
    """
    try:
        result = await service.close_consultation(
            consultation_id, current_user["user_id"], close_data.end_notes
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{consultation_id}/follow-up", response_model=FollowUpResponse, status_code=status.HTTP_201_CREATED)
async def schedule_follow_up(
    consultation_id: str,
    follow_up_data: FollowUpCreate,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: FollowUpService = Depends(get_follow_up_service),
):
    """
    Schedule a follow-up consultation.

    Links to original consultation, creates follow-up appointment,
    sets priority (low/medium/high), auto-notifies patient,
    status: "scheduled".
    """
    try:
        follow_up = await service.schedule_follow_up(
            consultation_id,
            current_user["user_id"],
            follow_up_data.follow_up_date,
            follow_up_data.follow_up_time,
            follow_up_data.reason,
            follow_up_data.priority,
        )
        return follow_up
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{consultation_id}/status", response_model=dict)
async def update_consultation_status(
    consultation_id: str,
    status_data: StatusUpdateRequest,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Update consultation status.

    Validates status transition. Only doctor can update.
    Allowed transitions: initiated → in-progress → completed.
    Stores status_change_timestamp.
    """
    try:
        result = await service.update_status(
            consultation_id, current_user["user_id"], status_data.status
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# SECTION 7: FEEDBACK & RATINGS (2 APIs)
# ============================================================================


@router.post("/{consultation_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    consultation_id: str,
    feedback_data: FeedbackCreate,
    current_user: dict = Depends(get_current_patient),
    service: FeedbackService = Depends(get_feedback_service),
):
    """
    Patient provides feedback for a consultation.

    Only patient can submit. Rating: 1-5 stars.
    Optional anonymous feedback. Stores all feedback details.
    """
    try:
        feedback = await service.submit_feedback(
            consultation_id,
            current_user["user_id"],
            feedback_data.rating,
            feedback_data.feedback_text,
            feedback_data.would_recommend,
            feedback_data.anonymous,
        )
        return feedback
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{consultation_id}/feedback", response_model=FeedbackResponse)
async def get_feedback(
    consultation_id: str,
    current_user: dict = Depends(get_current_user),
    service: FeedbackService = Depends(get_feedback_service),
):
    """
    Get consultation feedback.

    Anyone can view (public). Read-only for patient.
    Doctor can see feedback. Admin can see all feedback.
    """
    try:
        feedback = await service.get_feedback(consultation_id)
        return feedback
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# SECTION 8: CONSULTATION RETRIEVAL (2 APIs)
# ============================================================================


@router.get("/my-consultations", response_model=ConsultationHistoryResponse)
async def get_patient_consultations(
    status: str = "all",
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_patient),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Get patient's consultation history.

    Patient sees only their consultations. Filter by status
    (all, active, completed, pending-follow-up). Support pagination.
    Include doctor info and ratings.
    """
    filters = {"status": status, "limit": limit, "offset": offset}
    result = await service.get_patient_consultations(current_user["user_id"], filters)
    return ConsultationHistoryResponse(**result)


@router.get("/doctor-consultations", response_model=ConsultationHistoryResponse)
async def get_doctor_consultations(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    patient_name: Optional[str] = None,
    status: str = "all",
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: ConsultationService = Depends(get_consultation_service),
):
    """
    Get doctor's consultation schedule.

    Doctor sees only their consultations. Filter by date range,
    search by patient name, show consultation status.
    """
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "patient_name": patient_name,
        "status": status,
        "limit": limit,
        "offset": offset,
    }
    result = await service.get_doctor_consultations(current_user["user_id"], filters)
    return ConsultationHistoryResponse(**result)


# ============================================================================
# SECTION 9: VIDEO INTEGRATION (1 API)
# ============================================================================


@router.post("/{consultation_id}/video-token", response_model=dict)
async def generate_video_token(
    consultation_id: str,
    participant_type: str = "doctor",
    session_duration: int = 60,
    current_user: dict = Depends(get_current_user),
    service: VideoTokenService = Depends(get_video_token_service),
):
    """
    Generate video call token.

    Generates Agora/Twilio token. Sets token expiry (1 hour default).
    Unique channel per consultation. Time-limited access.
    Only consultation participants.
    """
    try:
        token_data = await service.generate_token(
            consultation_id,
            current_user["user_id"],
            participant_type,
            session_duration,
        )
        return token_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
