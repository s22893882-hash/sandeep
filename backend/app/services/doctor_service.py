"""Doctor service layer with business logic for doctor management."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.schemas.doctors import DoctorRegistrationRequest, WorkingHoursUpdate, AvailabilityStatusUpdate
import logging

logger = logging.getLogger(__name__)


class DoctorService:
    """Service class for doctor-related business logic."""

    def __init__(self):
        self.db = get_db()

    async def register_doctor(self, user_id: str, registration_data: DoctorRegistrationRequest) -> Dict[str, Any]:
        """Register a new doctor profile."""
        try:
            # Check if doctor profile already exists
            existing_doctor = await self.db.doctors.find_one({"user_id": user_id})
            if existing_doctor:
                raise ValueError("Doctor profile already exists for this user")

            # Get user details
            user = await self.db.users.find_one({"_id": user_id})
            if not user:
                raise ValueError("User not found")

            # Create doctor document
            doctor_doc = {
                "user_id": user_id,
                "license_number": registration_data.license_number,
                "license_expiry": registration_data.license_expiry,
                "specializations": [
                    {"name": spec.specialization_name, "expertise_level": spec.expertise_level}
                    for spec in registration_data.specialization
                ],
                "qualifications": [
                    {"degree": q.degree, "institution": q.institution, "year": q.year, "field": q.field}
                    for q in registration_data.qualifications
                ],
                "clinic_address": registration_data.clinic_address,
                "clinic_phone": registration_data.clinic_phone,
                "consultation_fee": registration_data.consultation_fee,
                "working_hours": {
                    day: {"start": hours.start, "end": hours.end} for day, hours in registration_data.working_hours.items()
                },
                "bio": registration_data.bio or "",
                "languages": registration_data.languages or [],
                "is_verified": False,
                "verification_date": None,
                "average_rating": 0.0,
                "review_count": 0,
                "availability_status": "available",
                "license_document_url": registration_data.license_document_url,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
            }

            # Insert into database
            result = await self.db.doctors.insert_one(doctor_doc)
            doctor_id = str(result.inserted_id)

            # Send verification email to admin
            # TODO: Implement actual email sending
            logger.info(f"Doctor {doctor_id} profile submitted for verification")

            return {"doctor_id": doctor_id, "message": "Profile submitted for verification"}

        except Exception as e:
            logger.error(f"Doctor registration failed: {str(e)}")
            raise

    async def verify_doctor(self, doctor_id: str, verified: bool, rejection_reason: Optional[str] = None) -> Dict[str, str]:
        """Verify or reject a doctor's profile."""
        try:
            update_data = {
                "is_verified": verified,
                "verification_date": datetime.utcnow() if verified else None,
                "updated_at": datetime.utcnow(),
            }

            if not verified and rejection_reason:
                update_data["rejection_reason"] = rejection_reason

            result = await self.db.doctors.update_one({"_id": doctor_id}, {"$set": update_data})

            if result.modified_count == 0:
                raise ValueError("Doctor not found")

            # Send email notification to doctor
            doctor = await self.db.doctors.find_one({"_id": doctor_id})
            user = await self.db.users.find_one({"_id": doctor["user_id"]})

            if verified:
                message = "Your doctor profile has been verified successfully"
            else:
                message = f"Your doctor profile was rejected: {rejection_reason}"

            # TODO: Implement actual email sending
            logger.info(f"Doctor {doctor_id} verification status: {verified}")

            return {"message": f"Doctor verified: {verified}" if verified else "Doctor rejected"}

        except Exception as e:
            logger.error(f"Doctor verification failed: {str(e)}")
            raise

    async def get_doctor_profile(self, doctor_id: str) -> Dict[str, Any]:
        """Get complete doctor profile with user details."""
        try:
            doctor = await self.db.doctors.find_one({"_id": doctor_id, "is_active": True})
            if not doctor:
                raise ValueError("Doctor not found")

            user = await self.db.users.find_one({"_id": doctor["user_id"]})
            if not user:
                raise ValueError("User profile not found")

            # Convert specializations to schema format
            doctor["specializations"] = [
                {"specialization_name": spec["name"], "expertise_level": spec["expertise_level"]}
                for spec in doctor.get("specializations", [])
            ]

            return {
                "doctor_id": doctor_id,
                "user": {
                    "user_id": str(user["_id"]),
                    "email": user["email"],
                    "phone": user["phone"],
                    "name": user["name"],
                    "role": user["role"],
                },
                "license_number": doctor["license_number"],
                "license_expiry": doctor["license_expiry"],
                "specialization": doctor["specializations"],
                "qualifications": doctor["qualifications"],
                "clinic_address": doctor["clinic_address"],
                "clinic_phone": doctor["clinic_phone"],
                "consultation_fee": doctor["consultation_fee"],
                "is_verified": doctor["is_verified"],
                "verification_date": doctor.get("verification_date"),
                "average_rating": doctor["average_rating"],
                "review_count": doctor["review_count"],
                "working_hours": doctor["working_hours"],
                "bio": doctor["bio"],
                "languages": doctor["languages"],
                "availability_status": doctor["availability_status"],
                "created_at": doctor["created_at"],
                "updated_at": doctor["updated_at"],
            }

        except Exception as e:
            logger.error(f"Get doctor profile failed: {str(e)}")
            raise

    async def update_doctor_profile(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update doctor profile."""
        try:
            doctor = await self.db.doctors.find_one({"user_id": user_id, "is_active": True})
            if not doctor:
                raise ValueError("Doctor not found")

            doctor_id = str(doctor["_id"])
            update_fields = {"updated_at": datetime.utcnow()}

            # Check if license is being updated
            if "license_number" in update_data or "license_expiry" in update_data:
                # Reset verification status
                update_data["is_verified"] = False
                update_data["verification_date"] = None

            # Handle specializations update
            if "specializations" in update_data:
                update_data["specializations"] = [
                    {"name": spec["name"], "expertise_level": spec["expertise_level"]}
                    for spec in update_data["specializations"]
                ]

            update_fields.update(update_data)

            result = await self.db.doctors.update_one({"_id": doctor_id}, {"$set": update_fields})

            if result.modified_count == 0:
                raise ValueError("No changes made")

            # Audit logging
            logger.info(f"Doctor {doctor_id} profile updated by user {user_id}")

            return await self.get_doctor_profile(doctor_id)

        except Exception as e:
            logger.error(f"Update doctor profile failed: {str(e)}")
            raise

    async def update_working_hours(self, user_id: str, working_hours_data: WorkingHoursUpdate) -> Dict[str, Any]:
        """Update doctor working hours."""
        try:
            doctor = await self.db.doctors.find_one({"user_id": user_id, "is_active": True})
            if not doctor:
                raise ValueError("Doctor not found")

            doctor_id = str(doctor["_id"])
            working_hours = {
                day: {"start": hours.start, "end": hours.end} for day, hours in working_hours_data.working_hours.items()
            }

            result = await self.db.doctors.update_one(
                {"_id": doctor_id},
                {
                    "$set": {
                        "working_hours": working_hours,
                        "is_available_weekends": working_hours_data.is_available_weekends,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            if result.modified_count == 0:
                raise ValueError("No changes made")

            return {
                "working_hours": working_hours,
                "is_available_weekends": working_hours_data.is_available_weekends,
                "message": "Working hours updated successfully",
            }

        except Exception as e:
            logger.error(f"Update working hours failed: {str(e)}")
            raise

    async def update_availability_status(self, user_id: str, status_data: AvailabilityStatusUpdate) -> Dict[str, Any]:
        """Update doctor availability status."""
        try:
            doctor = await self.db.doctors.find_one({"user_id": user_id, "is_active": True})
            if not doctor:
                raise ValueError("Doctor not found")

            doctor_id = str(doctor["_id"])
            update_data = {"availability_status": status_data.status, "updated_at": datetime.utcnow()}

            if status_data.status == "on-leave":
                update_data["return_date"] = status_data.return_date

            result = await self.db.doctors.update_one({"_id": doctor_id}, {"$set": update_data})

            if result.modified_count == 0:
                raise ValueError("No changes made")

            return {
                "status": status_data.status,
                "reason": status_data.reason,
                "return_date": status_data.return_date,
                "message": "Availability status updated",
            }

        except Exception as e:
            logger.error(f"Update availability status failed: {str(e)}")
            raise

    async def get_available_slots(
        self, doctor_id: str, target_date: datetime, duration_minutes: int = 30
    ) -> List[Dict[str, str]]:
        """Calculate available time slots for a doctor on a specific date."""
        try:
            doctor = await self.db.doctors.find_one({"_id": doctor_id, "is_active": True})
            if not doctor:
                raise ValueError("Doctor not found")

            # Get day of week
            day_name = target_date.strftime("%A")
            working_hours = doctor["working_hours"].get(day_name)

            if not working_hours:
                return []  # Doctor doesn't work on this day

            # Get existing appointments for this date
            booked_appointments = await self.db.appointments.find(
                {"doctor_id": doctor_id, "date": target_date, "status": {"$in": ["scheduled", "confirmed"]}}
            ).to_list(length=None)

            # Parse working hours
            import datetime as dt

            start_time = dt.datetime.strptime(working_hours["start"], "%H:%M").time()
            end_time = dt.datetime.strptime(working_hours["end"], "%H:%M").time()

            # Create occupied slots set
            occupied_slots = set()
            for appt in booked_appointments:
                appt_start = dt.datetime.strptime(appt["start_time"], "%H:%M").time()
                appt_end = dt.datetime.strptime(appt["end_time"], "%H:%M").time()
                occupied_slots.add((appt_start, appt_end))

            # Calculate available slots
            available_slots = []
            current_time = start_time
            duration = dt.timedelta(minutes=duration_minutes)

            while True:
                # Convert times to datetime for easier calculation
                current_dt = dt.datetime.combine(dt.date.min, current_time)
                end_slot_dt = current_dt + duration

                if end_slot_dt.time() > end_time:
                    break

                slot_start = current_time
                slot_end = end_slot_dt.time()

                # Check if slot is occupied
                is_occupied = any(
                    occupied_start <= slot_start < occupied_end or occupied_start < slot_end <= occupied_end
                    for occupied_start, occupied_end in occupied_slots
                )

                if not is_occupied:
                    available_slots.append(
                        {"start_time": slot_start.strftime("%H:%M"), "end_time": slot_end.strftime("%H:%M")}
                    )

                current_time = slot_end

            return available_slots

        except Exception as e:
            logger.error(f"Get available slots failed: {str(e)}")
            raise

    async def get_doctor_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get doctor statistics and performance metrics."""
        try:
            doctor = await self.db.doctors.find_one({"user_id": user_id, "is_active": True})
            if not doctor:
                raise ValueError("Doctor not found")

            doctor_id = str(doctor["_id"])

            # Get appointment statistics
            appointments = await self.db.appointments.find({"doctor_id": doctor_id}).to_list(length=None)

            total_appointments = len(appointments)
            completed_appointments = len([appt for appt in appointments if appt.get("status") == "completed"])

            # Get recent reviews
            recent_reviews = (
                await self.db.reviews.find({"doctor_id": doctor_id}).sort("date", -1).limit(5).to_list(length=None)
            )

            # Calculate average appointment duration (simplified)
            appointment_durations = []
            for appt in appointments:
                if "start_time" in appt and "end_time" in appt:
                    try:
                        start_dt = datetime.strptime(appt["start_time"], "%H:%M")
                        end_dt = datetime.strptime(appt["end_time"], "%H:%M")
                        duration = (end_dt - start_dt).total_seconds() / 60
                        appointment_durations.append(duration)
                    except:
                        continue

            avg_duration = int(sum(appointment_durations) / len(appointment_durations)) if appointment_durations else 30

            return {
                "total_appointments": total_appointments,
                "completed_appointments": completed_appointments,
                "avg_rating": doctor["average_rating"],
                "specializations": [spec.get("name", "") for spec in doctor.get("specializations", [])],
                "recent_reviews": recent_reviews,
                "appointment_duration_avg": avg_duration,
            }

        except Exception as e:
            logger.error(f"Get statistics failed: {str(e)}")
            raise

    async def search_doctors(
        self,
        query: Optional[str] = None,
        specialization: Optional[str] = None,
        rating_min: Optional[float] = None,
        consultation_fee_max: Optional[float] = None,
        location: Optional[str] = None,
        is_verified: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search doctors with filters and pagination."""
        try:
            # Build query filter
            filters = {"is_active": True}

            if is_verified is not None:
                filters["is_verified"] = is_verified

            if rating_min is not None:
                filters["average_rating"] = {"$gte": rating_min}

            if consultation_fee_max is not None:
                filters["consultation_fee"] = {"$lte": consultation_fee_max}

            if location:
                # Simplified location search (could use geospatial queries)
                filters["clinic_address"] = {"$regex": location, "$options": "i"}

            if specialization:
                filters["specializations.name"] = {"$regex": specialization, "$options": "i"}

            # Execute search
            doctors_cursor = self.db.doctors.find(filters).skip(offset).limit(limit)
            doctors = await doctors_cursor.to_list(length=limit)

            results = []
            for doctor in doctors:
                user = await self.db.users.find_one({"_id": doctor["user_id"]})
                if not user:
                    continue

                include_doctor = True

                # Text search on user name if query provided
                if query and user["name"]:
                    if query.lower() not in user["name"].lower():
                        include_doctor = False

                if include_doctor:
                    results.append(
                        {
                            "doctor_id": str(doctor["_id"]),
                            "user": {
                                "user_id": str(user["_id"]),
                                "email": user["email"],
                                "phone": user["phone"],
                                "name": user["name"],
                                "role": user["role"],
                            },
                            "specializations": [spec.get("name", "") for spec in doctor.get("specializations", [])],
                            "clinic_address": doctor["clinic_address"],
                            "consultation_fee": doctor["consultation_fee"],
                            "average_rating": doctor["average_rating"],
                            "review_count": doctor["review_count"],
                            "availability_status": doctor["availability_status"],
                            "is_verified": doctor["is_verified"],
                            "created_at": doctor["created_at"],
                        }
                    )

            return results

        except Exception as e:
            logger.error(f"Search doctors failed: {str(e)}")
            raise
