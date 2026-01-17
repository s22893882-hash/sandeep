"""Doctor availability checking logic."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import generate_id


class AvailabilityService:
    """Service for managing doctor availability."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def check_doctor_availability(self, doctor_id: str, appointment_date: str, appointment_time: str) -> bool:
        """Check if doctor is available at specified date and time."""
        try:
            appt_datetime = datetime.fromisoformat(f"{appointment_date}T{appointment_time}")
        except ValueError:
            return False

        if appt_datetime < datetime.utcnow():
            return False

        day_of_week = appt_datetime.weekday()
        appt_time = appt_datetime.time()

        availability = await self.db.doctor_availability.find_one(
            {
                "doctor_id": doctor_id,
                "day_of_week": day_of_week,
                "is_available": True,
            }
        )

        if not availability:
            return True

        try:
            start_time = datetime.strptime(availability["start_time"], "%H:%M").time()
            end_time = datetime.strptime(availability["end_time"], "%H:%M").time()
        except (KeyError, ValueError):
            return True

        if start_time <= appt_time < end_time:
            return await self.is_time_slot_free(doctor_id, appointment_date, appointment_time, 30)
        return False

    async def is_time_slot_free(self, doctor_id: str, appointment_date: str, appointment_time: str, duration: int) -> bool:
        """Check if time slot is free (no conflicting appointments)."""
        try:
            appt_datetime = datetime.fromisoformat(f"{appointment_date}T{appointment_time}")
        except ValueError:
            return False

        end_datetime = appt_datetime + timedelta(minutes=duration)

        conflicting = await self.db.appointments.find_one(
            {
                "doctor_id": doctor_id,
                "appointment_date": appointment_date,
                "status": {"$in": ["pending", "confirmed"]},
                "$or": [
                    {
                        "$and": [
                            {"appointment_time": {"$lte": appointment_time}},
                            {"appointment_time": {"$gte": appointment_time}},
                        ]
                    }
                ],
            }
        )

        if conflicting:
            try:
                existing_time = datetime.strptime(conflicting["appointment_time"], "%H:%M").time()
                existing_datetime = datetime.combine(
                    datetime.fromisoformat(conflicting["appointment_date"]).date(), existing_time
                )
                existing_end = existing_datetime + timedelta(minutes=conflicting.get("duration_minutes", 30))

                if appt_datetime < existing_end and end_datetime > existing_datetime:
                    return False
            except (ValueError, KeyError):
                pass

        return True

    async def get_available_slots(self, doctor_id: str, date: str) -> List[Dict[str, Any]]:
        """Get all available time slots for a doctor on a specific date."""
        try:
            target_date = datetime.fromisoformat(date)
        except ValueError:
            return []

        day_of_week = target_date.weekday()

        availability = await self.db.doctor_availability.find_one(
            {"doctor_id": doctor_id, "day_of_week": day_of_week, "is_available": True}
        )

        if not availability:
            return []

        try:
            start_time = datetime.strptime(availability["start_time"], "%H:%M").time()
            end_time = datetime.strptime(availability["end_time"], "%H:%M").time()
            slot_duration = availability.get("slot_duration_minutes", 30)
        except (KeyError, ValueError):
            return []

        slots = []
        current_time = datetime.combine(target_date.date(), start_time)
        end_datetime = datetime.combine(target_date.date(), end_time)

        while current_time < end_datetime:
            time_str = current_time.strftime("%H:%M")
            is_free = await self.is_time_slot_free(doctor_id, date, time_str, slot_duration)

            slots.append(
                {
                    "date": date,
                    "time": time_str,
                    "duration_minutes": slot_duration,
                    "is_available": is_free,
                }
            )

            current_time += timedelta(minutes=slot_duration)

        return slots

    async def validate_appointment_time(self, appointment_date: str, appointment_time: str) -> bool:
        """Validate that appointment date and time are in the future."""
        try:
            appt_datetime = datetime.fromisoformat(f"{appointment_date}T{appointment_time}")
            return appt_datetime > datetime.utcnow()
        except ValueError:
            return False

    async def create_doctor_availability(self, doctor_id: str, availability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create doctor availability schedule."""
        availability_id = generate_id("DA")
        now = datetime.utcnow()

        availability_doc = {
            "availability_id": availability_id,
            "doctor_id": doctor_id,
            "day_of_week": availability_data["day_of_week"],
            "start_time": availability_data["start_time"],
            "end_time": availability_data["end_time"],
            "slot_duration_minutes": availability_data.get("slot_duration_minutes", 30),
            "is_available": availability_data.get("is_available", True),
            "created_at": now,
            "updated_at": now,
        }

        await self.db.doctor_availability.insert_one(availability_doc)

        return {
            "availability_id": availability_id,
            "status": "created",
        }
