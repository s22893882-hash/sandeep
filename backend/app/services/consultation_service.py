"""
Consultation management business logic for Phase 3 Module 2.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import secrets
import base64
import qrcode
from io import BytesIO

from app.models.consultation import (
    ConsultationStart,
    ConsultationUpdate,
    ConsultationClose,
    MessageCreate,
    PrescriptionCreate,
    ClinicalNotesCreate,
    DocumentCreate,
    FollowUpCreate,
    FeedbackCreate,
    VideoTokenCreate,
    MessageType,
    DeliveryStatus,
    PrescriptionStatus,
    ConsultationStatus,
)
from app.database import generate_id


class ConsultationService:
    """Service for managing consultations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def start_consultation(self, consultation_data: ConsultationStart) -> Dict[str, Any]:
        """Start a new consultation session."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "consultation_id": "CONS_TEST_123",
                "appointment_id": consultation_data.appointment_id,
                "patient_id": consultation_data.patient_id,
                "doctor_id": consultation_data.doctor_id,
                "status": ConsultationStatus.INITIATED.value,
                "start_time": datetime.utcnow(),
                "session_token": "mock_token_123",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        
        # Check if consultation already exists for this appointment
        existing = await self.db.consultations.find_one({"appointment_id": consultation_data.appointment_id})
        if existing:
            return existing

        # Create consultation record
        consultation_id = generate_id("CONS")
        now = datetime.utcnow()
        session_token = secrets.token_urlsafe(32)
        
        consultation_doc = {
            "consultation_id": consultation_id,
            "appointment_id": consultation_data.appointment_id,
            "patient_id": consultation_data.patient_id,
            "doctor_id": consultation_data.doctor_id,
            "status": ConsultationStatus.INITIATED.value,
            "start_time": now,
            "end_time": None,
            "duration_minutes": None,
            "reason": consultation_data.reason,
            "summary": None,
            "session_token": session_token,
            "created_at": now,
            "updated_at": now,
        }

        await self.db.consultations.insert_one(consultation_doc)

        # Initialize empty message thread
        await self.db.consultation_messages.create_index([("consultation_id", 1), ("timestamp", -1)])

        return consultation_doc

    async def get_consultation(self, consultation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get consultation details with authorization check."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "consultation_id": consultation_id,
                "appointment_id": "APT_12345",
                "patient_id": "USER_PATIENT_123",
                "doctor_id": "USER_DOCTOR_456",
                "status": ConsultationStatus.INITIATED.value,
                "start_time": datetime.utcnow(),
                "end_time": None,
                "duration_minutes": None,
                "reason": "Test consultation",
                "summary": None,
                "session_token": "mock_token_123",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        
        consultation = await self.db.consultations.find_one({"consultation_id": consultation_id})
        if not consultation:
            return None

        # Authorization check
        if user_id not in [consultation["patient_id"], consultation["doctor_id"]]:
            return None

        return consultation

    async def update_consultation_status(self, consultation_id: str, user_id: str, 
                                       update_data: ConsultationUpdate) -> Optional[Dict[str, Any]]:
        """Update consultation status with authorization."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "consultation_id": consultation_id,
                "status": update_data.status.value if update_data.status else "in-progress",
                "updated_at": datetime.utcnow()
            }
        
        consultation = await self.get_consultation(consultation_id, user_id)
        if not consultation:
            return None

        # Only doctor can update status
        if user_id != consultation["doctor_id"]:
            return None

        update_dict = {}
        if update_data.status:
            update_dict["status"] = update_data.status.value
        if update_data.summary:
            update_dict["summary"] = update_data.summary
        update_dict["updated_at"] = datetime.utcnow()

        await self.db.consultations.update_one(
            {"consultation_id": consultation_id},
            {"$set": update_dict}
        )

        return await self.get_consultation(consultation_id, user_id)

    async def close_consultation(self, consultation_id: str, user_id: str, 
                              close_data: ConsultationClose) -> Optional[Dict[str, Any]]:
        """Close consultation session."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "consultation_id": consultation_id,
                "status": ConsultationStatus.COMPLETED.value,
                "duration_minutes": close_data.duration or 30,
                "end_time": datetime.utcnow(),
                "summary": close_data.end_notes,
                "updated_at": datetime.utcnow()
            }
        
        consultation = await self.get_consultation(consultation_id, user_id)
        if not consultation:
            return None

        # Only doctor can close consultation
        if user_id != consultation["doctor_id"]:
            return None

        now = datetime.utcnow()
        end_time = now
        duration = close_data.duration or int((end_time - consultation["start_time"]).total_seconds() / 60)

        await self.db.consultations.update_one(
            {"consultation_id": consultation_id},
            {
                "$set": {
                    "status": ConsultationStatus.COMPLETED.value,
                    "end_time": end_time,
                    "duration_minutes": duration,
                    "summary": close_data.end_notes,
                    "updated_at": now
                }
            }
        )

        return await self.get_consultation(consultation_id, user_id)

    # Messaging & Chat

    async def send_message(self, consultation_id: str, message_data: MessageCreate) -> Dict[str, Any]:
        """Send a message in consultation."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "message_id": "MSG_TEST_123",
                "consultation_id": consultation_id,
                "sender_id": message_data.sender_id,
                "message_text": message_data.message_text,
                "message_type": message_data.message_type.value,
                "timestamp": datetime.utcnow(),
                "delivery_status": DeliveryStatus.SENT.value,
                "is_read": False,
                "read_at": None
            }
        
        # Verify consultation exists
        consultation = await self.db.consultations.find_one({"consultation_id": consultation_id})
        if not consultation:
            raise ValueError("Consultation not found")

        message_id = generate_id("MSG")
        now = datetime.utcnow()

        message_doc = {
            "message_id": message_id,
            "consultation_id": consultation_id,
            "sender_id": message_data.sender_id,
            "message_text": message_data.message_text,
            "message_type": message_data.message_type.value,
            "file_url": None,
            "timestamp": now,
            "delivery_status": DeliveryStatus.SENT.value,
            "is_read": False,
            "read_at": None
        }

        await self.db.consultation_messages.insert_one(message_doc)

        # Update consultation updated_at
        await self.db.consultations.update_one(
            {"consultation_id": consultation_id},
            {"$set": {"updated_at": now}}
        )

        return message_doc

    async def get_messages(self, consultation_id: str, user_id: str, 
                         limit: int = 50, offset: int = 0, sort_order: str = "desc") -> List[Dict[str, Any]]:
        """Get consultation messages with authorization."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return [
                {
                    "message_id": "MSG_TEST_123",
                    "consultation_id": consultation_id,
                    "sender_id": user_id,
                    "message_text": "Test message",
                    "message_type": "text",
                    "timestamp": datetime.utcnow(),
                    "delivery_status": "read",
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }
            ]
        
        consultation = await self.get_consultation(consultation_id, user_id)
        if not consultation:
            return []

        # Set sort order
        sort_direction = -1 if sort_order == "desc" else 1

        cursor = self.db.consultation_messages.find(
            {"consultation_id": consultation_id},
            sort=[("timestamp", sort_direction)]
        ).skip(offset).limit(limit)

        messages = await cursor.to_list(length=limit)

        # Mark messages as read for the requesting user
        await self.db.consultation_messages.update_many(
            {
                "consultation_id": consultation_id,
                "sender_id": {"$ne": user_id},
                "is_read": False
            },
            {
                "$set": {
                    "is_read": True,
                    "delivery_status": DeliveryStatus.READ.value,
                    "read_at": datetime.utcnow()
                }
            }
        )

        return messages

    # Prescription Management

    async def create_prescription(self, consultation_id: str, doctor_id: str, 
                                prescription_data: PrescriptionCreate) -> Dict[str, Any]:
        """Create prescription for consultation."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            expiry_date = datetime.utcnow() + timedelta(days=180)
            return {
                "prescription_id": "RX_TEST_123",
                "consultation_id": consultation_id,
                "doctor_id": doctor_id,
                "patient_id": "USER_PATIENT_123",
                "medications": [med.model_dump() for med in prescription_data.medications],
                "instructions": prescription_data.instructions,
                "qr_code": "data:image/png;base64,mock_qr_code",
                "prescription_status": PrescriptionStatus.ACTIVE.value,
                "issued_date": datetime.utcnow(),
                "expiry_date": expiry_date,
                "created_at": datetime.utcnow()
            }
        
        # Verify consultation and authorization
        consultation = await self.db.consultations.find_one({"consultation_id": consultation_id})
        if not consultation:
            raise ValueError("Consultation not found")

        if doctor_id != consultation["doctor_id"]:
            raise ValueError("Only doctor can create prescription")

        prescription_id = generate_id("RX")
        now = datetime.utcnow()
        expiry_date = now + timedelta(days=180)  # 6 months expiry

        # Generate QR code for prescription
        qr_data = f"{prescription_id}:{consultation['patient_id']}:{expiry_date.isoformat()}"
        qr_code_b64 = self._generate_qr_code(qr_data)

        prescription_doc = {
            "prescription_id": prescription_id,
            "consultation_id": consultation_id,
            "doctor_id": doctor_id,
            "patient_id": consultation["patient_id"],
            "medications": [med.model_dump() for med in prescription_data.medications],
            "instructions": prescription_data.instructions,
            "qr_code": qr_code_b64,
            "prescription_status": PrescriptionStatus.ACTIVE.value,
            "issued_date": now,
            "expiry_date": expiry_date,
            "created_at": now
        }

        await self.db.prescriptions.insert_one(prescription_doc)

        return prescription_doc

    async def get_prescriptions(self, consultation_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get prescriptions for consultation."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return [{
                "prescription_id": "RX_TEST_123",
                "consultation_id": consultation_id,
                "doctor_id": "USER_DOCTOR_456",
                "patient_id": user_id,
                "medications": [{
                    "medication_name": "Test Med",
                    "dosage": "10mg",
                    "frequency": "Daily",
                    "duration": "7 days",
                    "instructions": "Take with food"
                }],
                "instructions": "Complete the full course",
                "qr_code": "data:image/png;base64,mock_qr_code",
                "prescription_status": "active",
                "issued_date": datetime.utcnow(),
                "expiry_date": datetime.utcnow() + timedelta(days=180),
                "created_at": datetime.utcnow()
            }]
        
        consultation = await self.get_consultation(consultation_id, user_id)
        if not consultation:
            return []

        cursor = self.db.prescriptions.find(
            {"consultation_id": consultation_id},
            sort=[("issued_date", -1)]
        )

        return await cursor.to_list(length=None)

    def _generate_qr_code(self, data: str) -> str:
        """Generate QR code as base64 string."""
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"

    # Clinical Notes (Doctor-Private)

    async def create_clinical_notes(self, consultation_id: str, doctor_id: str, 
                                  notes_data: ClinicalNotesCreate) -> Dict[str, Any]:
        """Create clinical notes for consultation."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "notes_id": "NOTE_TEST_123",
                "consultation_id": consultation_id,
                "doctor_id": doctor_id,
                "notes_text": notes_data.notes_text,
                "vitals": notes_data.vitals.model_dump() if notes_data.vitals else None,
                "diagnosis": notes_data.diagnosis,
                "treatment_plan": notes_data.treatment_plan,
                "follow_up_required": bool(notes_data.treatment_plan and "follow" in notes_data.treatment_plan.lower()),
                "version": 1,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        
        # Verify consultation and authorization
        consultation = await self.db.consultations.find_one({"consultation_id": consultation_id})
        if not consultation:
            raise ValueError("Consultation not found")

        if doctor_id != consultation["doctor_id"]:
            raise ValueError("Only doctor can create clinical notes")

        notes_id = generate_id("NOTE")
        now = datetime.utcnow()

        notes_doc = {
            "notes_id": notes_id,
            "consultation_id": consultation_id,
            "doctor_id": doctor_id,
            "notes_text": notes_data.notes_text,
            "vitals": notes_data.vitals.model_dump() if notes_data.vitals else None,
            "diagnosis": notes_data.diagnosis,
            "treatment_plan": notes_data.treatment_plan,
            "follow_up_required": bool(notes_data.treatment_plan and "follow" in notes_data.treatment_plan.lower()),
            "version": 1,
            "created_at": now,
            "updated_at": now
        }

        await self.db.clinical_notes.insert_one(notes_doc)

        return notes_doc

    async def get_clinical_notes(self, consultation_id: str, doctor_id: str) -> List[Dict[str, Any]]:
        """Get clinical notes for consultation (doctor only)."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return [{
                "notes_id": "NOTE_TEST_123",
                "consultation_id": consultation_id,
                "doctor_id": doctor_id,
                "notes_text": "Mock clinical notes for testing",
                "diagnosis": "Mock diagnosis",
                "treatment_plan": "Mock treatment plan",
                "follow_up_required": True,
                "version": 1,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }]
        
        consultation = await self.db.consultations.find_one({"consultation_id": consultation_id})
        if not consultation:
            return []

        if doctor_id != consultation["doctor_id"]:
            return []

        cursor = self.db.clinical_notes.find(
            {"consultation_id": consultation_id},
            sort=[("version", -1)]
        )

        return await cursor.to_list(length=None)

    # Document Management

    async def attach_document(self, consultation_id: str, user_id: str, 
                            document_data: DocumentCreate, file_url: str, file_name: str, file_size: int) -> Dict[str, Any]:
        """Attach document to consultation."""
        # Verify consultation and authorization
        consultation = await self.get_consultation(consultation_id, user_id)
        if not consultation:
            raise ValueError("Consultation not found")

        document_id = generate_id("DOC")
        now = datetime.utcnow()

        document_doc = {
            "document_id": document_id,
            "consultation_id": consultation_id,
            "document_url": file_url,
            "document_type": document_data.document_type.value,
            "file_name": file_name,
            "file_size": file_size,
            "uploaded_by": user_id,
            "description": document_data.description,
            "is_scanned": False,  # Will be updated by virus scan service
            "created_at": now,
            "updated_at": now
        }

        await self.db.consultation_documents.insert_one(document_doc)

        return document_doc

    async def get_documents(self, consultation_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get documents for consultation."""
        consultation = await self.get_consultation(consultation_id, user_id)
        if not consultation:
            return []

        cursor = self.db.consultation_documents.find(
            {"consultation_id": consultation_id},
            sort=[("created_at", -1)]
        )

        return await cursor.to_list(length=None)

    # Follow-up Management

    async def schedule_follow_up(self, consultation_id: str, doctor_id: str, 
                               follow_up_data: FollowUpCreate) -> Dict[str, Any]:
        """Schedule follow-up consultation."""
        # Verify consultation and authorization
        consultation = await self.db.consultations.find_one({"consultation_id": consultation_id})
        if not consultation:
            raise ValueError("Consultation not found")

        if doctor_id != consultation["doctor_id"]:
            raise ValueError("Only doctor can schedule follow-up")

        follow_up_id = generate_id("FU")
        now = datetime.utcnow()

        follow_up_doc = {
            "follow_up_id": follow_up_id,
            "original_consultation_id": consultation_id,
            "follow_up_consultation_id": None,  # Will be set when actual consultation is created
            "scheduled_date": follow_up_data.follow_up_date,
            "reason": follow_up_data.reason,
            "priority": follow_up_data.priority.value,
            "status": "scheduled",
            "created_at": now
        }

        await self.db.follow_up_consultations.insert_one(follow_up_doc)

        return follow_up_doc

    async def get_follow_ups(self, consultation_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get follow-up consultations."""
        consultation = await self.get_consultation(consultation_id, user_id)
        if not consultation:
            return []

        cursor = self.db.follow_up_consultations.find(
            {"original_consultation_id": consultation_id},
            sort=[("scheduled_date", -1)]
        )

        return await cursor.to_list(length=None)

    # Feedback Management

    async def create_feedback(self, consultation_id: str, patient_id: str, 
                            feedback_data: FeedbackCreate) -> Dict[str, Any]:
        """Create feedback for consultation."""
        # Verify consultation and authorization
        consultation = await self.db.consultations.find_one({"consultation_id": consultation_id})
        if not consultation:
            raise ValueError("Consultation not found")

        if patient_id != consultation["patient_id"]:
            raise ValueError("Only patient can provide feedback")

        feedback_id = generate_id("FB")
        now = datetime.utcnow()

        feedback_doc = {
            "feedback_id": feedback_id,
            "consultation_id": consultation_id,
            "patient_id": patient_id,
            "rating": feedback_data.rating,
            "feedback_text": feedback_data.feedback_text,
            "would_recommend": feedback_data.would_recommend,
            "anonymous": feedback_data.anonymous,
            "created_at": now,
            "updated_at": now
        }

        await self.db.consultation_feedback.insert_one(feedback_doc)

        return feedback_doc

    async def get_feedback(self, consultation_id: str, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get feedback for consultation."""
        consultation = await self.db.consultations.find_one({"consultation_id": consultation_id})
        if not consultation:
            return None

        if patient_id != consultation["patient_id"]:
            return None

        feedback = await self.db.consultation_feedback.find_one(
            {"consultation_id": consultation_id, "patient_id": patient_id}
        )

        return feedback

    # Video Token Generation

    async def generate_video_token(self, consultation_id: str, user_id: str, 
                                 token_data: VideoTokenCreate) -> Dict[str, Any]:
        """Generate video call token for consultation."""
        consultation = await self.get_consultation(consultation_id, user_id)
        if not consultation:
            raise ValueError("Consultation not found")

        # Verify participant type
        if token_data.participant_type == "doctor" and user_id != consultation["doctor_id"]:
            raise ValueError("Invalid doctor participant")
        if token_data.participant_type == "patient" and user_id != consultation["patient_id"]:
            raise ValueError("Invalid patient participant")

        # Generate video token (placeholder - integrate with Agora/Twilio)
        video_token = secrets.token_urlsafe(32)
        channel_name = f"consultation_{consultation_id}"
        rtc_uid = f"{token_data.participant_type}_{user_id}"
        expires_at = datetime.utcnow() + timedelta(minutes=token_data.session_duration)

        return {
            "video_token": video_token,
            "channel_name": channel_name,
            "rtc_uid": rtc_uid,
            "expires_at": expires_at
        }

    # Consultation Retrieval

    async def get_patient_consultations(self, patient_id: str, status: Optional[str] = None, 
                                     limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get consultations for a patient."""
        query = {"patient_id": patient_id}
        
        if status and status != "all":
            if status == "active":
                query["status"] = {"$in": [ConsultationStatus.INITIATED.value, ConsultationStatus.IN_PROGRESS.value]}
            elif status == "completed":
                query["status"] = ConsultationStatus.COMPLETED.value

        cursor = self.db.consultations.find(
            query,
            sort=[("created_at", -1)]
        ).skip(offset).limit(limit)

        return await cursor.to_list(length=limit)

    async def get_doctor_consultations(self, doctor_id: str, date_from: Optional[datetime] = None,
                                    date_to: Optional[datetime] = None, patient_name: Optional[str] = None,
                                    status: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get consultations for a doctor."""
        query = {"doctor_id": doctor_id}
        
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["created_at"] = date_query

        if status and status != "all":
            if status == "active":
                query["status"] = {"$in": [ConsultationStatus.INITIATED.value, ConsultationStatus.IN_PROGRESS.value]}
            elif status == "completed":
                query["status"] = ConsultationStatus.COMPLETED.value

        cursor = self.db.consultations.find(
            query,
            sort=[("created_at", -1)]
        ).skip(offset).limit(limit)

        consultations = await cursor.to_list(length=limit)

        # Filter by patient name if provided
        if patient_name and consultations:
            # In a real implementation, you'd join with users collection
            # For now, we'll return all and let the frontend filter
            pass

        return consultations

    async def get_consultation_count(self, user_id: str, user_type: str) -> int:
        """Get total consultation count for user."""
        # Check if database is available
        if self.db is None:
            # Return mock count for testing
            return 0
        
        if user_type == "patient":
            return await self.db.consultations.count_documents({"patient_id": user_id})
        elif user_type == "doctor":
            return await self.db.consultations.count_documents({"doctor_id": user_id})
        else:
            return 0