"""Appointment management business logic."""
from typing import Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.appointment import (
    AppointmentUpdateRequest,
    AppointmentStatus,
)
from app.database import generate_id
from app.services.availability_service import AvailabilityService


class AppointmentService:
    """Service for managing appointments."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.availability_service = AvailabilityService(database)

    async def book_appointment(
        self,
        patient_id: str,
        doctor_id: str,
        appointment_date: str,
        appointment_time: str,
        reason: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Book a new appointment."""
        if not await self.availability_service.validate_appointment_time(appointment_date, appointment_time):
            raise ValueError("Appointment must be scheduled in the future")

        if not await self.availability_service.check_doctor_availability(doctor_id, appointment_date, appointment_time):
            raise ValueError("Doctor is not available at the requested time")

        if not await self.availability_service.is_time_slot_free(doctor_id, appointment_date, appointment_time, 30):
            raise ValueError("Time slot is already booked")

        appointment_id = generate_id("APT")
        now = datetime.utcnow()

        appointment_doc = {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "duration_minutes": 30,
            "reason": reason,
            "notes": notes,
            "status": AppointmentStatus.pending.value,
            "cancellation_reason": None,
            "created_at": now,
            "updated_at": now,
            "cancelled_at": None,
        }

        await self.db.appointments.insert_one(appointment_doc)

        return {
            "appointment_id": appointment_id,
            "status": AppointmentStatus.pending.value,
            "confirmation_details": {
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "doctor_id": doctor_id,
            },
        }

    async def get_appointment(self, appointment_id: str, user_id: str, user_role: str) -> Optional[Dict[str, Any]]:
        """Get appointment details with authorization check."""
        appointment = await self.db.appointments.find_one({"appointment_id": appointment_id})

        if not appointment:
            return None

        if user_role == "admin":
            return appointment

        if user_role == "patient":
            patient = await self.db.patients.find_one({"user_id": user_id})
            if patient and appointment["patient_id"] == patient.get("patient_id"):
                return appointment

        if user_role == "doctor":
            doctor = await self.db.doctors.find_one({"user_id": user_id})
            if doctor and appointment["doctor_id"] == doctor.get("doctor_id"):
                return appointment

        return None

    async def get_patient_appointments(
        self, patient_id: str, status: Optional[str] = None, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """Get patient appointments with optional status filter and pagination."""
        query = {"patient_id": patient_id}

        if status:
            query["status"] = status

        total = await self.db.appointments.count_documents(query)

        cursor = self.db.appointments.find(query).sort("appointment_date", -1).skip(offset).limit(limit)

        appointments = await cursor.to_list(length=limit)

        return {
            "appointments": appointments,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def update_appointment(self, appointment_id: str, update_data: AppointmentUpdateRequest) -> Optional[Dict[str, Any]]:
        """Update appointment details."""
        appointment = await self.db.appointments.find_one({"appointment_id": appointment_id})

        if not appointment:
            return None

        if appointment["status"] in [
            AppointmentStatus.completed.value,
            AppointmentStatus.cancelled.value,
        ]:
            raise ValueError("Cannot update completed or cancelled appointments")

        update_dict = {}

        if update_data.notes is not None:
            update_dict["notes"] = update_data.notes

        if update_data.appointment_date is not None and update_data.appointment_time is not None:
            if not await self.availability_service.validate_appointment_time(
                update_data.appointment_date, update_data.appointment_time
            ):
                raise ValueError("Appointment must be scheduled in the future")

            if not await self.availability_service.check_doctor_availability(
                appointment["doctor_id"],
                update_data.appointment_date,
                update_data.appointment_time,
            ):
                raise ValueError("Doctor is not available at the requested time")

            if not await self.availability_service.is_time_slot_free(
                appointment["doctor_id"],
                update_data.appointment_date,
                update_data.appointment_time,
                30,
            ):
                raise ValueError("Time slot is already booked")

            update_dict["appointment_date"] = update_data.appointment_date
            update_dict["appointment_time"] = update_data.appointment_time

        if not update_dict:
            return appointment

        update_dict["updated_at"] = datetime.utcnow()

        await self.db.appointments.update_one({"appointment_id": appointment_id}, {"$set": update_dict})

        return await self.db.appointments.find_one({"appointment_id": appointment_id})

    async def cancel_appointment(self, appointment_id: str, cancellation_reason: str) -> Dict[str, Any]:
        """Cancel an appointment."""
        appointment = await self.db.appointments.find_one({"appointment_id": appointment_id})

        if not appointment:
            raise ValueError("Appointment not found")

        if appointment["status"] not in [
            AppointmentStatus.pending.value,
            AppointmentStatus.confirmed.value,
        ]:
            raise ValueError("Can only cancel pending or confirmed appointments")

        now = datetime.utcnow()

        await self.db.appointments.update_one(
            {"appointment_id": appointment_id},
            {
                "$set": {
                    "status": AppointmentStatus.cancelled.value,
                    "cancellation_reason": cancellation_reason,
                    "cancelled_at": now,
                    "updated_at": now,
                }
            },
        )

        return {
            "appointment_id": appointment_id,
            "status": AppointmentStatus.cancelled.value,
            "cancelled_at": now,
            "message": "Appointment cancelled successfully",
        }

    async def reschedule_appointment(self, appointment_id: str, new_date: str, new_time: str) -> Optional[Dict[str, Any]]:
        """Reschedule an appointment to a new date and time."""
        appointment = await self.db.appointments.find_one({"appointment_id": appointment_id})

        if not appointment:
            return None

        if appointment["status"] not in [
            AppointmentStatus.pending.value,
            AppointmentStatus.confirmed.value,
        ]:
            raise ValueError("Can only reschedule pending or confirmed appointments")

        if not await self.availability_service.validate_appointment_time(new_date, new_time):
            raise ValueError("Appointment must be scheduled in the future")

        if not await self.availability_service.check_doctor_availability(appointment["doctor_id"], new_date, new_time):
            raise ValueError("Doctor is not available at the requested time")

        if not await self.availability_service.is_time_slot_free(appointment["doctor_id"], new_date, new_time, 30):
            raise ValueError("Time slot is already booked")

        await self.db.appointments.update_one(
            {"appointment_id": appointment_id},
            {
                "$set": {
                    "appointment_date": new_date,
                    "appointment_time": new_time,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        return await self.db.appointments.find_one({"appointment_id": appointment_id})

    async def get_appointment_history(self, patient_id: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Get appointment history for a patient with pagination."""
        query = {"patient_id": patient_id}

        total = await self.db.appointments.count_documents(query)

        cursor = self.db.appointments.find(query).sort("appointment_date", -1).skip(offset).limit(limit)

        appointments = await cursor.to_list(length=limit)

        return {
            "appointments": appointments,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
