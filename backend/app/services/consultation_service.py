"""Consultation management business logic."""
from typing import List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.consultation import (
    ConsultationCreate,
    ConsultationStatus,
)
from app.database import generate_id, format_mongo_doc, format_mongo_docs


class ConsultationService:
    """Service for managing consultations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def start_consultation(self, data: ConsultationCreate) -> Dict[str, Any]:
        """Initialize a consultation session."""
        consultation_id = generate_id("CON")
        now = datetime.utcnow()
        consultation_doc = {
            "consultation_id": consultation_id,
            "patient_id": data.patient_id,
            "doctor_id": data.doctor_id,
            "appointment_id": data.appointment_id,
            "status": ConsultationStatus.active.value,
            "start_time": now,
            "created_at": now,
            "updated_at": now,
        }
        await self.db.consultations.insert_one(consultation_doc)
        return format_mongo_doc(consultation_doc)

    async def get_consultation(self, consultation_id: str) -> Dict[str, Any]:
        """Get consultation details."""
        consultation = await self.db.consultations.find_one({"consultation_id": consultation_id})
        if not consultation:
            raise ValueError("Consultation not found")
        return format_mongo_doc(consultation)

    async def send_message(self, consultation_id: str, sender_id: str, message: str, msg_type: str = "text") -> Dict[str, Any]:
        """Send a consultation message."""
        message_id = generate_id("MSG")
        message_doc = {
            "message_id": message_id,
            "consultation_id": consultation_id,
            "sender_id": sender_id,
            "message": message,
            "timestamp": datetime.utcnow(),
            "type": msg_type,
        }
        await self.db.consultation_messages.insert_one(message_doc)
        return format_mongo_doc(message_doc)

    async def get_messages(self, consultation_id: str) -> List[Dict[str, Any]]:
        """Get consultation chat history."""
        cursor = self.db.consultation_messages.find({"consultation_id": consultation_id}).sort("timestamp", 1)
        docs = await cursor.to_list(length=None)
        return format_mongo_docs(docs)

    async def add_prescription(
        self, consultation_id: str, doctor_id: str, patient_id: str, medications: List[dict]
    ) -> Dict[str, Any]:
        """Doctor adds a prescription."""
        prescription_id = generate_id("PRC")
        prescription_doc = {
            "prescription_id": prescription_id,
            "consultation_id": consultation_id,
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "medications": medications,
            "issued_at": datetime.utcnow(),
        }
        await self.db.prescriptions.insert_one(prescription_doc)
        return prescription_doc

    async def get_prescriptions(self, consultation_id: str) -> List[Dict[str, Any]]:
        """Get prescriptions for a consultation."""
        cursor = self.db.prescriptions.find({"consultation_id": consultation_id})
        return await cursor.to_list(length=None)

    async def add_notes(self, consultation_id: str, doctor_id: str, notes: str) -> Dict[str, Any]:
        """Add clinical notes."""
        note_id = generate_id("NTE")
        note_doc = {
            "note_id": note_id,
            "consultation_id": consultation_id,
            "doctor_id": doctor_id,
            "notes": notes,
            "timestamp": datetime.utcnow(),
        }
        await self.db.clinical_notes.insert_one(note_doc)
        return note_doc

    async def get_notes(self, consultation_id: str) -> List[Dict[str, Any]]:
        """Get clinical notes for a consultation."""
        cursor = self.db.clinical_notes.find({"consultation_id": consultation_id})
        return await cursor.to_list(length=None)

    async def attach_document(self, consultation_id: str, doc_url: str, file_type: str, uploaded_by: str) -> Dict[str, Any]:
        """Attach medical documents/reports."""
        document_id = generate_id("DOC")
        doc_doc = {
            "document_id": document_id,
            "consultation_id": consultation_id,
            "document_url": doc_url,
            "file_type": file_type,
            "uploaded_by": uploaded_by,
            "timestamp": datetime.utcnow(),
        }
        await self.db.consultation_documents.insert_one(doc_doc)
        return doc_doc

    async def get_documents(self, consultation_id: str) -> List[Dict[str, Any]]:
        """Get attached documents for a consultation."""
        cursor = self.db.consultation_documents.find({"consultation_id": consultation_id})
        return await cursor.to_list(length=None)

    async def close_consultation(self, consultation_id: str) -> Dict[str, Any]:
        """End a consultation."""
        now = datetime.utcnow()
        consultation = await self.db.consultations.find_one({"consultation_id": consultation_id})
        if not consultation:
            raise ValueError("Consultation not found")

        start_time = consultation.get("start_time")
        duration = 0
        if start_time:
            duration = int((now - start_time).total_seconds() / 60)

        await self.db.consultations.update_one(
            {"consultation_id": consultation_id},
            {"$set": {"status": ConsultationStatus.completed.value, "end_time": now, "duration": duration, "updated_at": now}},
        )
        return {"status": "closed", "consultation_id": consultation_id, "duration": duration}

    async def schedule_follow_up(self, consultation_id: str, follow_up_date: str) -> Dict[str, Any]:
        """Schedule follow-up consultation."""
        # This could interact with AppointmentService
        return {"status": "follow_up_scheduled", "consultation_id": consultation_id, "date": follow_up_date}

    async def get_patient_consultations(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve patient's consultations."""
        cursor = self.db.consultations.find({"patient_id": patient_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def get_doctor_consultations(self, doctor_id: str) -> List[Dict[str, Any]]:
        """Retrieve doctor's consultations."""
        cursor = self.db.consultations.find({"doctor_id": doctor_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def provide_feedback(self, consultation_id: str, patient_id: str, rating: int, comments: str) -> Dict[str, Any]:
        """Patient provides feedback."""
        feedback_doc = {
            "consultation_id": consultation_id,
            "patient_id": patient_id,
            "rating": rating,
            "comments": comments,
            "timestamp": datetime.utcnow(),
        }
        await self.db.consultation_feedback.insert_one(feedback_doc)
        return feedback_doc

    async def get_feedback(self, consultation_id: str) -> Dict[str, Any]:
        """Get consultation feedback."""
        return await self.db.consultation_feedback.find_one({"consultation_id": consultation_id})

    async def generate_video_token(self, consultation_id: str) -> Dict[str, Any]:
        """Generate video call token."""
        # Mock token generation
        return {"consultation_id": consultation_id, "token": f"mock_token_{consultation_id}", "app_id": "mock_app_id"}

    async def update_status(self, consultation_id: str, status: str) -> Dict[str, Any]:
        """Update consultation status."""
        await self.db.consultations.update_one(
            {"consultation_id": consultation_id}, {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return {"consultation_id": consultation_id, "status": status}
