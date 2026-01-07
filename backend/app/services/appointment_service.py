"""Appointment management business logic."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentStatus,
)
from app.database import generate_id


class AppointmentService:
    """Service for managing appointments."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def get_doctor_availability(self, doctor_id: str, date: str) -> List[Dict[str, Any]]:
        """Get doctor's available slots for a specific date."""
        cursor = self.db.appointment_slots.find({"doctor_id": doctor_id, "date": date, "available": True})
        return await cursor.to_list(length=None)

    async def book_appointment(self, appointment_data: AppointmentCreate) -> Dict[str, Any]:
        """Book a new appointment."""
        # Check if slot is available
        slot = await self.db.appointment_slots.find_one(
            {
                "doctor_id": appointment_data.doctor_id,
                "date": appointment_data.appointment_date,
                "time": appointment_data.time_slot,
                "available": True,
            }
        )

        if not slot:
            raise ValueError("Requested time slot is not available")

        appointment_id = generate_id("APT")
        now = datetime.utcnow()

        appointment_doc = {
            "appointment_id": appointment_id,
            "patient_id": appointment_data.patient_id,
            "doctor_id": appointment_data.doctor_id,
            "appointment_date": appointment_data.appointment_date,
            "time_slot": appointment_data.time_slot,
            "status": AppointmentStatus.scheduled.value,
            "notes": appointment_data.notes,
            "reminder_sent": False,
            "created_at": now,
            "updated_at": now,
        }

        # Use a transaction if possible, but for simplicity here:
        await self.db.appointments.insert_one(appointment_doc)
        await self.db.appointment_slots.update_one(
            {"_id": slot["_id"]}, {"$set": {"available": False, "booked_by": appointment_data.patient_id}}
        )

        return appointment_doc

    async def get_patient_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve patient's appointments."""
        cursor = self.db.appointments.find({"patient_id": patient_id}).sort("appointment_date", -1)
        return await cursor.to_list(length=None)

    async def get_doctor_schedule(self, doctor_id: str) -> List[Dict[str, Any]]:
        """Retrieve doctor's appointment schedule."""
        cursor = self.db.appointments.find({"doctor_id": doctor_id}).sort("appointment_date", 1)
        return await cursor.to_list(length=None)

    async def reschedule_appointment(self, appointment_id: str, update_data: AppointmentUpdate) -> Dict[str, Any]:
        """Reschedule an existing appointment."""
        appointment = await self.db.appointments.find_one({"appointment_id": appointment_id})
        if not appointment:
            raise ValueError("Appointment not found")

        if appointment["status"] == AppointmentStatus.completed.value:
            raise ValueError("Cannot reschedule a completed appointment")

        # Record history
        history_id = generate_id("RH")
        history_doc = {
            "history_id": history_id,
            "appointment_id": appointment_id,
            "old_date": appointment["appointment_date"],
            "old_time": appointment["time_slot"],
            "new_date": update_data.appointment_date or appointment["appointment_date"],
            "new_time": update_data.time_slot or appointment["time_slot"],
            "reason": update_data.notes,
            "timestamp": datetime.utcnow(),
        }
        await self.db.reschedule_history.insert_one(history_doc)

        # Update slot availability
        # Free old slot
        await self.db.appointment_slots.update_one(
            {"doctor_id": appointment["doctor_id"], "date": appointment["appointment_date"], "time": appointment["time_slot"]},
            {"$set": {"available": True, "booked_by": None}},
        )

        # Book new slot
        new_date = update_data.appointment_date or appointment["appointment_date"]
        new_time = update_data.time_slot or appointment["time_slot"]

        slot = await self.db.appointment_slots.find_one(
            {"doctor_id": appointment["doctor_id"], "date": new_date, "time": new_time, "available": True}
        )
        if not slot:
            # Rollback? For simplicity, we just raise error.
            # In production, this should be handled more robustly.
            raise ValueError("New requested time slot is not available")

        await self.db.appointment_slots.update_one(
            {"_id": slot["_id"]}, {"$set": {"available": False, "booked_by": appointment["patient_id"]}}
        )

        # Update appointment
        update_dict = {
            "appointment_date": new_date,
            "time_slot": new_time,
            "status": AppointmentStatus.rescheduled.value,
            "updated_at": datetime.utcnow(),
        }
        await self.db.appointments.update_one({"appointment_id": appointment_id}, {"$set": update_dict})

        return await self.db.appointments.find_one({"appointment_id": appointment_id})

    async def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Cancel an appointment."""
        appointment = await self.db.appointments.find_one({"appointment_id": appointment_id})
        if not appointment:
            raise ValueError("Appointment not found")

        await self.db.appointments.update_one(
            {"appointment_id": appointment_id},
            {"$set": {"status": AppointmentStatus.cancelled.value, "updated_at": datetime.utcnow()}},
        )

        # Free the slot
        await self.db.appointment_slots.update_one(
            {"doctor_id": appointment["doctor_id"], "date": appointment["appointment_date"], "time": appointment["time_slot"]},
            {"$set": {"available": True, "booked_by": None}},
        )

        return {"status": "cancelled", "appointment_id": appointment_id}

    async def complete_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Mark appointment as completed."""
        result = await self.db.appointments.update_one(
            {"appointment_id": appointment_id},
            {"$set": {"status": AppointmentStatus.completed.value, "updated_at": datetime.utcnow()}},
        )
        if result.matched_count == 0:
            raise ValueError("Appointment not found")
        return {"status": "completed", "appointment_id": appointment_id}

    async def get_appointment_details(self, appointment_id: str) -> Dict[str, Any]:
        """Get appointment details."""
        appointment = await self.db.appointments.find_one({"appointment_id": appointment_id})
        if not appointment:
            raise ValueError("Appointment not found")
        return appointment

    async def set_reminder(self, appointment_id: str) -> Dict[str, Any]:
        """Set appointment reminder."""
        await self.db.appointments.update_one(
            {"appointment_id": appointment_id}, {"$set": {"reminder_sent": True, "updated_at": datetime.utcnow()}}
        )
        return {"status": "reminder_set", "appointment_id": appointment_id}

    async def get_doctor_stats(self, doctor_id: str) -> Dict[str, Any]:
        """Get doctor appointment statistics."""
        total = await self.db.appointments.count_documents({"doctor_id": doctor_id})
        completed = await self.db.appointments.count_documents(
            {"doctor_id": doctor_id, "status": AppointmentStatus.completed.value}
        )
        cancelled = await self.db.appointments.count_documents(
            {"doctor_id": doctor_id, "status": AppointmentStatus.cancelled.value}
        )
        upcoming = await self.db.appointments.count_documents(
            {
                "doctor_id": doctor_id,
                "status": AppointmentStatus.scheduled.value,
                "appointment_date": {"$gte": datetime.utcnow().strftime("%Y-%m-%d")},
            }
        )

        return {
            "doctor_id": doctor_id,
            "total_appointments": total,
            "completed_appointments": completed,
            "cancelled_appointments": cancelled,
            "upcoming_appointments": upcoming,
        }

    async def check_conflicts(self, doctor_id: str, date: str, time: str) -> bool:
        """Check for scheduling conflicts."""
        existing = await self.db.appointments.find_one(
            {
                "doctor_id": doctor_id,
                "appointment_date": date,
                "time_slot": time,
                "status": {"$in": [AppointmentStatus.scheduled.value, AppointmentStatus.rescheduled.value]},
            }
        )
        return existing is not None

    async def bulk_reschedule(self, doctor_id: str, old_date: str, new_date: str) -> Dict[str, Any]:
        """Bulk reschedule appointments from one date to another."""
        cursor = self.db.appointments.find(
            {"doctor_id": doctor_id, "appointment_date": old_date, "status": AppointmentStatus.scheduled.value}
        )
        appointments = await cursor.to_list(length=None)

        count = 0
        for appt in appointments:
            try:
                # Try to reschedule to same time on new date
                await self.reschedule_appointment(
                    appt["appointment_id"], AppointmentUpdate(appointment_date=new_date, time_slot=appt["time_slot"])
                )
                count += 1
            except Exception:
                continue

        return {"rescheduled_count": count, "total_found": len(appointments)}

    async def get_calendar_view(self, doctor_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get calendar view of appointments."""
        cursor = self.db.appointments.find(
            {"doctor_id": doctor_id, "appointment_date": {"$gte": start_date, "$lte": end_date}}
        )
        return await cursor.to_list(length=None)

    async def add_notes(self, appointment_id: str, notes: str) -> Dict[str, Any]:
        """Add appointment notes."""
        await self.db.appointments.update_one(
            {"appointment_id": appointment_id}, {"$set": {"notes": notes, "updated_at": datetime.utcnow()}}
        )
        return {"status": "notes_added", "appointment_id": appointment_id}

    async def get_upcoming_notifications(self) -> List[Dict[str, Any]]:
        """Get upcoming appointment alerts."""
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        cursor = self.db.appointments.find(
            {"appointment_date": tomorrow, "status": AppointmentStatus.scheduled.value, "reminder_sent": False}
        )
        return await cursor.to_list(length=None)
