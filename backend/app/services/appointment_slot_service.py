"""Appointment slot management service for doctor schedules."""
from datetime import datetime, timedelta
from typing import List, Dict
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.appointment import AppointmentSlotCreate, AppointmentSlotResponse, WorkingHoursUpdate


class AppointmentSlotService:
    """Service for managing doctor appointment slots and working hours."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.appointment_slots_collection = database.appointment_slots

    async def create_appointment_slot(self, slot_data: AppointmentSlotCreate) -> AppointmentSlotResponse:
        """Create a new appointment slot."""
        slot_doc = {
            "slot_id": str(ObjectId()),
            "doctor_id": slot_data.doctor_id,
            "date": slot_data.date,
            "start_time": slot_data.start_time,
            "end_time": slot_data.end_time,
            "is_available": slot_data.is_available,
            "slot_type": slot_data.slot_type,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        await self.appointment_slots_collection.insert_one(slot_doc)

        return AppointmentSlotResponse(
            slot_id=slot_doc["slot_id"],
            doctor_id=slot_doc["doctor_id"],
            date=slot_doc["date"],
            start_time=slot_doc["start_time"],
            end_time=slot_doc["end_time"],
            is_available=slot_doc["is_available"],
            slot_type=slot_doc["slot_type"],
            created_at=slot_doc["created_at"],
            updated_at=slot_doc["updated_at"],
        )

    async def bulk_create_slots(self, slots_data: List[AppointmentSlotCreate]) -> List[AppointmentSlotResponse]:
        """Create multiple appointment slots at once."""
        slot_docs = []
        for slot_data in slots_data:
            slot_doc = {
                "slot_id": str(ObjectId()),
                "doctor_id": slot_data.doctor_id,
                "date": slot_data.date,
                "start_time": slot_data.start_time,
                "end_time": slot_data.end_time,
                "is_available": slot_data.is_available,
                "slot_type": slot_data.slot_type,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            slot_docs.append(slot_doc)

        if slot_docs:
            await self.appointment_slots_collection.insert_many(slot_docs)

        return [
            AppointmentSlotResponse(
                slot_id=doc["slot_id"],
                doctor_id=doc["doctor_id"],
                date=doc["date"],
                start_time=doc["start_time"],
                end_time=doc["end_time"],
                is_available=doc["is_available"],
                slot_type=doc["slot_type"],
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
            )
            for doc in slot_docs
        ]

    async def update_working_hours(self, working_hours_data: WorkingHoursUpdate) -> bool:
        """Update doctor's working hours."""
        # This would typically update a doctor profile or working_hours collection
        # For now, we'll store it in the appointment_slots collection with a special record
        working_hours_doc = {
            "working_hours_id": str(ObjectId()),
            "doctor_id": working_hours_data.doctor_id,
            "working_hours": working_hours_data.working_hours,
            "updated_at": datetime.now(),
            "is_working_hours": True,
        }

        await self.appointment_slots_collection.insert_one(working_hours_doc)
        return True

    async def get_doctor_working_hours(self, doctor_id: str) -> Dict[str, List[str]]:
        """Get doctor's working hours."""
        # Find the most recent working hours record
        working_hours_doc = await self.appointment_slots_collection.find_one(
            {"doctor_id": doctor_id, "is_working_hours": True}, sort=[("updated_at", -1)]
        )

        if working_hours_doc:
            return working_hours_doc["working_hours"]

        # Return default working hours
        return {
            "monday": ["09:00-17:00"],
            "tuesday": ["09:00-17:00"],
            "wednesday": ["09:00-17:00"],
            "thursday": ["09:00-17:00"],
            "friday": ["09:00-17:00"],
            "saturday": [],
            "sunday": [],
        }

    async def get_available_slots(self, doctor_id: str, date: str) -> List[AppointmentSlotResponse]:
        """Get available slots for a doctor on a specific date."""
        slots = (
            await self.appointment_slots_collection.find({"doctor_id": doctor_id, "date": date, "is_available": True})
            .sort("start_time", 1)
            .to_list(None)
        )

        return [
            AppointmentSlotResponse(
                slot_id=slot["slot_id"],
                doctor_id=slot["doctor_id"],
                date=slot["date"],
                start_time=slot["start_time"],
                end_time=slot["end_time"],
                is_available=slot["is_available"],
                slot_type=slot["slot_type"],
                created_at=slot["created_at"],
                updated_at=slot.get("updated_at"),
            )
            for slot in slots
        ]

    async def mark_slot_unavailable(self, slot_id: str) -> bool:
        """Mark a slot as unavailable (e.g., when booked)."""
        result = await self.appointment_slots_collection.update_one(
            {"slot_id": slot_id}, {"$set": {"is_available": False, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0

    async def generate_weekly_slots(self, doctor_id: str, start_date: str) -> List[AppointmentSlotResponse]:
        """Generate a week's worth of appointment slots based on working hours."""
        working_hours = await self.get_doctor_working_hours(doctor_id)

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        generated_slots = []

        for day_offset in range(7):
            current_date = start_dt + timedelta(days=day_offset)
            day_name = current_date.strftime("%A").lower()

            if day_name in working_hours and working_hours[day_name]:
                for time_range in working_hours[day_name]:
                    start_time_str, end_time_str = time_range.split("-")

                    # Generate 30-minute slots within the time range
                    current_time = datetime.strptime(start_time_str, "%H:%M")
                    end_time = datetime.strptime(end_time_str, "%H:%M")

                    while current_time + timedelta(minutes=30) <= end_time:
                        slot_start = current_time.strftime("%H:%M")
                        slot_end = (current_time + timedelta(minutes=30)).strftime("%H:%M")

                        slot_data = AppointmentSlotCreate(
                            doctor_id=doctor_id,
                            date=current_date.strftime("%Y-%m-%d"),
                            start_time=slot_start,
                            end_time=slot_end,
                            is_available=True,
                            slot_type="general",
                        )

                        generated_slot = await self.create_appointment_slot(slot_data)
                        generated_slots.append(generated_slot)

                        current_time += timedelta(minutes=30)

        return generated_slots


# Dependency function to get appointment slot service
async def get_appointment_slot_service():
    """Dependency to get appointment slot service instance."""
    from app.database import get_database

    db = get_database()
    return AppointmentSlotService(db)
