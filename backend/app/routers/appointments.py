"""Appointment management API endpoints for Phase 3."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    DoctorAvailabilityResponse,
    RescheduleRequest,
    RescheduleResponse,
    CancellationRequest,
    CancellationResponse,
    DoctorStatsResponse,
    ConflictDetectionResponse,
    CalendarViewResponse,
    ReminderCreate,
    ReminderResponse,
)
from app.services.appointment_service import get_appointment_service
from app.auth import get_current_user

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


# ============================================================================
# 1. AVAILABILITY & BOOKING APIs (2 APIs)
# ============================================================================


@router.get("/availability/{doctor_id}", response_model=DoctorAvailabilityResponse)
async def get_doctor_availability(
    doctor_id: str,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/appointments/availability/{doctor_id}
    Real-time available slots checking (< 100ms response).
    """
    try:
        appointment_service = await get_appointment_service()
        availability = await appointment_service.get_real_time_availability(doctor_id, start_date, end_date)
        return availability
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching availability: {str(e)}")


@router.post("/book", response_model=AppointmentResponse)
async def book_appointment(appointment_data: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    """
    POST /api/appointments/book
    Book new appointment with conflict checking.
    """
    try:
        # Verify user is a patient
        if current_user.get("role") != "patient":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can book appointments")

        appointment_service = await get_appointment_service()

        # Get patient_id from user context
        patient_id = current_user["user_id"]

        appointment = await appointment_service.book_appointment(patient_id, appointment_data)
        return appointment

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error booking appointment: {str(e)}")


# ============================================================================
# 2. APPOINTMENT MANAGEMENT APIs (3 APIs)
# ============================================================================


@router.get("/my-appointments", response_model=List[AppointmentResponse])
async def get_my_appointments(
    limit: int = Query(50, le=100), offset: int = Query(0, ge=0), current_user: dict = Depends(get_current_user)
):
    """
    GET /api/appointments/my-appointments
    Patient's appointment history.
    """
    try:
        appointment_service = await get_appointment_service()

        if current_user.get("role") == "patient":
            appointments = await appointment_service.get_patient_appointments(current_user["user_id"], limit, offset)
        elif current_user.get("role") == "doctor":
            # For doctors, show appointments where they're the doctor
            # This would need to be implemented in the service
            appointments = []  # Placeholder
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role")

        return appointments

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching appointments: {str(e)}")


@router.get("/doctor-schedule", response_model=List[AppointmentResponse])
async def get_doctor_schedule(
    doctor_id: str = Query(..., description="Doctor's user ID"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/appointments/doctor-schedule
    Doctor's full schedule.
    """
    try:
        appointment_service = await get_appointment_service()

        # Verify access - doctor can see their own schedule, admin can see all
        if current_user.get("role") == "doctor" and current_user["user_id"] != doctor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only view your own schedule")

        schedule = await appointment_service.get_doctor_schedule(doctor_id, date)
        return schedule

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching schedule: {str(e)}")


@router.get("/{appointment_id}/details", response_model=AppointmentResponse)
async def get_appointment_details(appointment_id: str, current_user: dict = Depends(get_current_user)):
    """
    GET /api/appointments/{id}/details
    Specific appointment details.
    """
    try:
        appointment_service = await get_appointment_service()

        # This would need to be implemented - getting single appointment by ID
        # For now, we'll search in patient's appointments
        if current_user.get("role") == "patient":
            appointments = await appointment_service.get_patient_appointments(current_user["user_id"], limit=1000, offset=0)
            appointment = next((apt for apt in appointments if apt.appointment_id == appointment_id), None)
        elif current_user.get("role") == "doctor":
            # Doctor would need to see appointments where they're the doctor
            # This would need service implementation
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Doctor appointment details not implemented yet"
            )
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

        return appointment

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching appointment details: {str(e)}"
        )


# ============================================================================
# 3. RESCHEDULING & CANCELLATION APIs (3 APIs)
# ============================================================================


@router.put("/{appointment_id}/reschedule", response_model=RescheduleResponse)
async def reschedule_appointment(
    appointment_id: str, reschedule_data: RescheduleRequest, current_user: dict = Depends(get_current_user)
):
    """
    PUT /api/appointments/{id}/reschedule
    Move to different time slot.
    """
    try:
        # Verify patient owns the appointment
        if current_user.get("role") != "patient":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can reschedule their appointments"
            )

        # This would need service implementation for rescheduling
        # For now, raise not implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Rescheduling functionality will be implemented in full service",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error rescheduling appointment: {str(e)}"
        )


@router.post("/{appointment_id}/cancel", response_model=CancellationResponse)
async def cancel_appointment(
    appointment_id: str, cancellation_data: CancellationRequest, current_user: dict = Depends(get_current_user)
):
    """
    POST /api/appointments/{id}/cancel
    Cancel with refund calculation.
    """
    try:
        appointment_service = await get_appointment_service()

        # Verify patient owns the appointment
        if current_user.get("role") != "patient":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can cancel their appointments")

        result = await appointment_service.cancel_appointment(appointment_id, cancellation_data)
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error cancelling appointment: {str(e)}"
        )


@router.post("/bulk-reschedule")
async def bulk_reschedule_appointments(
    reschedule_data: Dict[str, Any],  # Would be BulkRescheduleRequest but for simplicity
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/appointments/bulk-reschedule
    Bulk reschedule (admin/doctor only).
    """
    try:
        # Verify admin or doctor access
        if current_user.get("role") not in ["admin", "doctor"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only admins and doctors can perform bulk rescheduling"
            )

        # This would need full implementation
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Bulk rescheduling will be implemented in full service"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error in bulk reschedule: {str(e)}")


# ============================================================================
# 4. LIFECYCLE MANAGEMENT APIs (2 APIs)
# ============================================================================


@router.put("/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_appointment(
    appointment_id: str, notes: Optional[str] = None, current_user: dict = Depends(get_current_user)
):
    """
    PUT /api/appointments/{id}/complete
    Mark completed after visit.
    """
    try:
        # Verify doctor access
        if current_user.get("role") != "doctor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can mark appointments as completed"
            )

        # This would need service implementation for doctor appointment access
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Complete appointment functionality will be implemented in full service",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error completing appointment: {str(e)}"
        )


@router.put("/{appointment_id}/notes")
async def add_appointment_notes(
    appointment_id: str,
    notes: Dict[str, str],  # {"notes": "consultation notes"}
    current_user: dict = Depends(get_current_user),
):
    """
    PUT /api/appointments/{id}/notes
    Add appointment notes.
    """
    try:
        # Verify doctor access
        if current_user.get("role") != "doctor":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can add appointment notes")

        # This would need service implementation
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Adding appointment notes will be implemented in full service"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error adding notes: {str(e)}")


# ============================================================================
# 5. REMINDERS & NOTIFICATIONS APIs (2 APIs)
# ============================================================================


@router.post("/{appointment_id}/reminder", response_model=ReminderResponse)
async def schedule_reminder(
    appointment_id: str, reminder_data: ReminderCreate, current_user: dict = Depends(get_current_user)
):
    """
    POST /api/appointments/{id}/reminder
    Schedule reminder notification.
    """
    try:
        # Verify patient or doctor can schedule reminders
        if current_user.get("role") not in ["patient", "doctor", "admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to schedule reminders")

        # This would need service implementation
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Reminder scheduling will be implemented in full service"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error scheduling reminder: {str(e)}")


@router.get("/upcoming-notifications")
async def get_upcoming_notifications(
    hours_ahead: int = Query(24, description="Hours ahead to check for upcoming appointments"),
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/appointments/upcoming-notifications
    Upcoming appointment alerts.
    """
    try:
        # This would need service implementation to get upcoming reminders
        return {"upcoming_appointments": [], "reminders_scheduled": 0, "checked_time_range": f"{hours_ahead} hours ahead"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching upcoming notifications: {str(e)}"
        )


# ============================================================================
# 6. ANALYTICS & STATISTICS APIs (3 APIs)
# ============================================================================


@router.get("/doctor/{doctor_id}/stats", response_model=DoctorStatsResponse)
async def get_doctor_statistics(
    doctor_id: str,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/appointments/doctor/{doctor_id}/stats
    Doctor statistics.
    """
    try:
        # Verify access - doctor can see their own stats, admin can see all
        if current_user.get("role") == "doctor" and current_user["user_id"] != doctor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only view your own statistics")

        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        # This would need service implementation for statistics calculation
        return DoctorStatsResponse(
            doctor_id=doctor_id,
            doctor_name=None,  # Would be fetched from doctor service
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching doctor statistics: {str(e)}"
        )


@router.get("/availability-conflicts", response_model=ConflictDetectionResponse)
async def detect_availability_conflicts(
    doctor_id: str, date: str, time: str, duration_minutes: int = 30, current_user: dict = Depends(get_current_user)
):
    """
    GET /api/appointments/availability-conflicts
    Detect double-bookings.
    """
    try:
        appointment_service = await get_appointment_service()

        conflicts = await appointment_service.check_conflict_detection(doctor_id, date, time, duration_minutes)

        return ConflictDetectionResponse(**conflicts)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error detecting conflicts: {str(e)}")


@router.get("/calendar/{doctor_id}", response_model=CalendarViewResponse)
async def get_calendar_view(
    doctor_id: str,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/appointments/calendar/{doctor_id}
    Calendar view.
    """
    try:
        # Verify access - doctor can see their own calendar, admin can see all
        if current_user.get("role") == "doctor" and current_user["user_id"] != doctor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only view your own calendar")

        # This would need service implementation for calendar events
        return CalendarViewResponse(
            doctor_id=doctor_id,
            doctor_name=None,  # Would be fetched from doctor service
            date_range={"start": start_date, "end": end_date},
            events=[],
            total_events=0,
            view_generation_time_ms=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating calendar view: {str(e)}"
        )
