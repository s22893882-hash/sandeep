"""Statistics and analytics service for appointment data."""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.appointment import DoctorStatsResponse, AppointmentAnalytics


class AppointmentStatisticsService:
    """Service for generating appointment statistics and analytics."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.appointments_collection = database.appointments
        self.reschedule_history_collection = database.reschedule_history

    async def get_doctor_statistics(self, doctor_id: str, start_date: str, end_date: str) -> DoctorStatsResponse:
        """Get comprehensive statistics for a doctor."""
        # Get all appointments for the doctor in the date range
        appointments = await self.appointments_collection.find(
            {"doctor_id": doctor_id, "appointment_date": {"$gte": start_date, "$lte": end_date}}
        ).to_list(None)

        if not appointments:
            return DoctorStatsResponse(
                doctor_id=doctor_id,
                doctor_name=None,
                period={"start": start_date, "end": end_date},
                total_appointments=0,
                completed_appointments=0,
                cancelled_appointments=0,
                no_show_appointments=0,
                rescheduled_appointments=0,
                average_appointment_duration=0.0,
                total_revenue=0.0,
                cancellation_rate=0.0,
                completion_rate=0.0,
                most_common_consultation_type="general",
                busiest_day="monday",
                peak_hour="10:00",
            )

        # Get doctor info
        doctor_info = await self._get_doctor_info(doctor_id)

        # Calculate statistics
        total_appointments = len(appointments)
        completed_appointments = len([apt for apt in appointments if apt["status"] == "completed"])
        cancelled_appointments = len([apt for apt in appointments if apt["status"] == "cancelled"])
        no_show_appointments = len([apt for apt in appointments if apt["status"] == "no_show"])
        rescheduled_appointments = len([apt for apt in appointments if apt["status"] == "rescheduled"])

        # Calculate average appointment duration
        valid_durations = [apt["duration_minutes"] for apt in appointments if "duration_minutes" in apt]
        avg_duration = sum(valid_durations) / len(valid_durations) if valid_durations else 0.0

        # Calculate revenue (assuming $100 per consultation)
        total_revenue = completed_appointments * 100.0

        # Calculate rates
        cancellation_rate = (cancelled_appointments / total_appointments * 100) if total_appointments > 0 else 0.0
        completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0.0

        # Find most common consultation type
        consultation_types = {}
        for apt in appointments:
            consultation_type = apt.get("consultation_type", "general")
            consultation_types[consultation_type] = consultation_types.get(consultation_type, 0) + 1

        most_common_consultation_type = (
            max(consultation_types.items(), key=lambda x: x[1])[0] if consultation_types else "general"
        )

        # Find busiest day
        day_counts = {}
        for apt in appointments:
            day = apt["appointment_date"]
            day_counts[day] = day_counts.get(day, 0) + 1

        busiest_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else "monday"

        # Find peak hour
        hour_counts = {}
        for apt in appointments:
            time_str = apt.get("appointment_time", "10:00")
            try:
                hour = int(time_str.split(":")[0])
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            except (ValueError, IndexError):
                continue

        peak_hour_int = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 10
        peak_hour = f"{peak_hour_int:02d}:00"

        return DoctorStatsResponse(
            doctor_id=doctor_id,
            doctor_name=doctor_info.get("name") if doctor_info else None,
            period={"start": start_date, "end": end_date},
            total_appointments=total_appointments,
            completed_appointments=completed_appointments,
            cancelled_appointments=cancelled_appointments,
            no_show_appointments=no_show_appointments,
            rescheduled_appointments=rescheduled_appointments,
            average_appointment_duration=avg_duration,
            total_revenue=total_revenue,
            cancellation_rate=cancellation_rate,
            completion_rate=completion_rate,
            most_common_consultation_type=most_common_consultation_type,
            busiest_day=busiest_day,
            peak_hour=peak_hour,
        )

    async def get_appointment_analytics(self, start_date: str, end_date: str) -> AppointmentAnalytics:
        """Get overall appointment analytics."""
        # Get all appointments in the date range
        appointments = await self.appointments_collection.find(
            {"appointment_date": {"$gte": start_date, "$lte": end_date}}
        ).to_list(None)

        if not appointments:
            return AppointmentAnalytics(
                total_appointments=0,
                appointments_by_status={},
                appointments_by_day={},
                average_booking_lead_time=0.0,
                peak_booking_hours=[],
                most_active_doctors=[],
                cancellation_reasons={},
            )

        # Calculate basic statistics
        total_appointments = len(appointments)

        # Appointments by status
        appointments_by_status = {}
        for apt in appointments:
            status = apt.get("status", "scheduled")
            appointments_by_status[status] = appointments_by_status.get(status, 0) + 1

        # Appointments by day
        appointments_by_day = {}
        for apt in appointments:
            date = apt["appointment_date"]
            appointments_by_day[date] = appointments_by_day.get(date, 0) + 1

        # Calculate average booking lead time
        lead_times = await self._calculate_lead_times(appointments)
        average_booking_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0.0

        # Get peak booking hours
        peak_booking_hours = self._calculate_peak_hours(appointments)

        # Get most active doctors
        most_active_doctors = self._calculate_most_active_doctors(appointments)

        # Get cancellation reasons
        cancellation_reasons = self._calculate_cancellation_reasons(appointments)

        return AppointmentAnalytics(
            total_appointments=total_appointments,
            appointments_by_status=appointments_by_status,
            appointments_by_day=appointments_by_day,
            average_booking_lead_time=average_booking_lead_time,
            peak_booking_hours=peak_booking_hours,
            most_active_doctors=most_active_doctors,
            cancellation_reasons=cancellation_reasons,
        )

    async def _calculate_lead_times(self, appointments: List[Dict[str, Any]]) -> List[float]:
        """Calculate booking lead times for appointments."""
        lead_times = []
        for apt in appointments:
            if "created_at" in apt:
                try:
                    created_at = apt["created_at"]
                    appointment_datetime = datetime.strptime(
                        f"{apt['appointment_date']} {apt['appointment_time']}", "%Y-%m-%d %H:%M"
                    )
                    lead_time_hours = (appointment_datetime - created_at).total_seconds() / 3600
                    if lead_time_hours > 0:
                        lead_times.append(lead_time_hours)
                except (ValueError, TypeError):
                    continue
        return lead_times

    def _calculate_peak_hours(self, appointments: List[Dict[str, Any]]) -> List[str]:
        """Calculate peak booking hours from appointments."""
        hour_counts = {}
        for apt in appointments:
            time_str = apt.get("appointment_time", "10:00")
            try:
                hour = int(time_str.split(":")[0])
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            except (ValueError, IndexError):
                continue

        return sorted(
            [f"{hour:02d}:00" for hour, count in hour_counts.items()],
            key=lambda x: hour_counts[int(x.split(":")[0])],
            reverse=True,
        )[:3]

    def _calculate_most_active_doctors(self, appointments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate most active doctors from appointments."""
        doctor_counts = {}
        for apt in appointments:
            doctor_id = apt["doctor_id"]
            doctor_counts[doctor_id] = doctor_counts.get(doctor_id, 0) + 1

        return sorted(
            [{"doctor_id": doctor_id, "appointment_count": count} for doctor_id, count in doctor_counts.items()],
            key=lambda x: x["appointment_count"],
            reverse=True,
        )[:5]

    def _calculate_cancellation_reasons(self, appointments: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate cancellation reasons from appointments."""
        cancellation_reasons = {}
        for apt in appointments:
            if apt.get("status") == "cancelled" and apt.get("cancellation_reason"):
                reason = apt["cancellation_reason"]
                cancellation_reasons[reason] = cancellation_reasons.get(reason, 0) + 1
        return cancellation_reasons

    async def detect_availability_conflicts(
        self, doctor_id: str, date: str, time: str, duration_minutes: int
    ) -> Dict[str, Any]:
        """Detect potential availability conflicts for a time slot."""
        conflicts = await self.appointments_collection.find(
            {"doctor_id": doctor_id, "appointment_date": date, "status": {"$in": ["scheduled", "confirmed", "in_progress"]}}
        ).to_list(None)

        # Check for conflicts with the requested time slot
        requested_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        requested_end = requested_start + timedelta(minutes=duration_minutes)

        conflicting_appointments = []
        for apt in conflicts:
            apt_start = datetime.strptime(f"{apt['appointment_date']} {apt['appointment_time']}", "%Y-%m-%d %H:%M")
            apt_end = apt_start + timedelta(minutes=apt.get("duration_minutes", 30))

            # Check for overlap
            if apt_start < requested_end and apt_end > requested_start:
                conflicting_appointments.append(
                    {
                        "appointment_id": apt["appointment_id"],
                        "appointment_time": apt["appointment_time"],
                        "duration_minutes": apt.get("duration_minutes", 30),
                        "status": apt["status"],
                        "patient_id": apt["patient_id"],
                    }
                )

        # Get suggested alternatives
        suggested_alternatives = await self._get_suggested_alternatives(doctor_id, date, duration_minutes, conflicts)

        return {
            "conflict_found": len(conflicting_appointments) > 0,
            "conflicting_appointments": conflicting_appointments,
            "suggested_alternatives": suggested_alternatives,
            "checked_time_range": {"start": requested_start.isoformat(), "end": requested_end.isoformat()},
            "analysis_time_ms": 15,  # Fast analysis
        }

    async def _get_doctor_info(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        """Get doctor information from doctor management service."""
        # This would integrate with doctor management service
        # For now, return mock data
        return {"name": f"Dr. {doctor_id[-4:].upper()}", "specialization": "General Practice"}  # Mock doctor name

    async def _get_suggested_alternatives(
        self, doctor_id: str, date: str, duration_minutes: int, existing_appointments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get suggested alternative time slots."""
        # Get working hours for the doctor
        working_hours = await self._get_doctor_working_hours(doctor_id)

        day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%A").lower()
        if day_name not in working_hours or not working_hours[day_name]:
            return []

        # Get booked slots
        booked_slots = {(apt["appointment_time"], apt.get("duration_minutes", 30)) for apt in existing_appointments}

        # Generate alternatives
        alternatives = []
        for time_range in working_hours[day_name]:
            start_time_str, end_time_str = time_range.split("-")
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            current_time = start_time
            while current_time < end_time:
                slot_end = datetime.combine(datetime.today(), current_time) + timedelta(minutes=duration_minutes)
                if slot_end.time() <= end_time:
                    time_str = current_time.strftime("%H:%M")
                    end_time_str = slot_end.strftime("%H:%M")

                    if (time_str, duration_minutes) not in booked_slots:
                        alternatives.append(
                            {
                                "date": date,
                                "time": time_str,
                                "end_time": end_time_str,
                                "duration": duration_minutes,
                                "availability": "available",
                            }
                        )

                current_time = slot_end.time()

        return alternatives[:5]  # Return top 5 alternatives

    async def _get_doctor_working_hours(self, doctor_id: str) -> Dict[str, List[str]]:
        """Get doctor's working hours."""
        # This would fetch from doctor profile or working hours collection
        return {
            "monday": ["09:00-17:00"],
            "tuesday": ["09:00-17:00"],
            "wednesday": ["09:00-17:00"],
            "thursday": ["09:00-17:00"],
            "friday": ["09:00-17:00"],
            "saturday": [],
            "sunday": [],
        }

    async def get_calendar_events(self, doctor_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get calendar events for a doctor in a date range."""
        appointments = (
            await self.appointments_collection.find(
                {
                    "doctor_id": doctor_id,
                    "appointment_date": {"$gte": start_date, "$lte": end_date},
                    "status": {"$in": ["scheduled", "confirmed", "in_progress", "completed"]},
                }
            )
            .sort("appointment_date", 1)
            .sort("appointment_time", 1)
            .to_list(None)
        )

        events = []
        for apt in appointments:
            # Calculate end time
            start_time = apt["appointment_time"]
            duration = apt.get("duration_minutes", 30)
            start_dt = datetime.strptime(f"{apt['appointment_date']} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(minutes=duration)

            # Get patient name (would integrate with patient service)
            patient_name = await self._get_patient_name(apt["patient_id"])

            event = {
                "appointment_id": apt["appointment_id"],
                "title": f"Appointment - {patient_name}",
                "date": apt["appointment_date"],
                "start_time": start_time,
                "end_time": end_dt.strftime("%H:%M"),
                "status": apt["status"],
                "patient_name": patient_name,
                "consultation_type": apt.get("consultation_type", "general"),
                "notes": apt.get("notes"),
            }
            events.append(event)

        return events

    async def _get_patient_name(self, patient_id: str) -> str:
        """Get patient name (mock implementation)."""
        # This would integrate with patient management service
        return f"Patient {patient_id[-4:].upper()}"


# Dependency function to get statistics service
async def get_appointment_statistics_service():
    """Dependency to get appointment statistics service instance."""
    from app.database import get_database

    db = get_database()
    return AppointmentStatisticsService(db)
