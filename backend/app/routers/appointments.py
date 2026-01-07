"""Appointment management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime

from app.auth import get_current_user, get_current_doctor_or_admin
from app.models.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    DoctorStats,
)
from app.services.appointment_service import AppointmentService
from app.database import get_database

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


def get_appointment_service(db=Depends(get_database)) -> AppointmentService:
    """Get appointment service instance."""
    return AppointmentService(db)


@router.get("/availability/{doctor_id}", response_model=list)
async def get_availability(
    doctor_id: str,
    date: str = datetime.utcnow().strftime("%Y-%m-%d"),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Get doctor's available slots."""
    return await service.get_doctor_availability(doctor_id, date)


@router.post("/book", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment_data: AppointmentCreate,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Book a new appointment."""
    try:
        # Ensure patient_id matches current user or is set correctly
        # In a real app, we'd verify the relationship between user and patient
        return await service.book_appointment(appointment_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-appointments", response_model=List[AppointmentResponse])
async def get_my_appointments(
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Retrieve patient's appointments."""
    # Assuming user_id is used as patient_id or we can look it up
    # For now, we use user_id directly as a placeholder
    return await service.get_patient_appointments(current_user["user_id"])


@router.get("/doctor-schedule", response_model=List[AppointmentResponse])
async def get_doctor_schedule(
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Doctor's appointment schedule."""
    return await service.get_doctor_schedule(current_user["user_id"])


@router.put("/{id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    id: str,
    update_data: AppointmentUpdate,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Reschedule appointment."""
    try:
        return await service.reschedule_appointment(id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/cancel", response_model=dict)
async def cancel_appointment(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Cancel appointment."""
    try:
        return await service.cancel_appointment(id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{id}/complete", response_model=dict)
async def complete_appointment(
    id: str,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Mark appointment as completed."""
    try:
        return await service.complete_appointment(id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{id}/details", response_model=AppointmentResponse)
async def get_appointment_details(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Get appointment details."""
    try:
        return await service.get_appointment_details(id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/reminder", response_model=dict)
async def set_reminder(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Set appointment reminder."""
    return await service.set_reminder(id)


@router.get("/doctor/{doctor_id}/stats", response_model=DoctorStats)
async def get_doctor_stats(
    doctor_id: str,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Doctor appointment statistics."""
    return await service.get_doctor_stats(doctor_id)


@router.get("/availability-conflicts", response_model=dict)
async def check_conflicts(
    doctor_id: str,
    date: str,
    time: str,
    service: AppointmentService = Depends(get_appointment_service),
):
    """Check scheduling conflicts."""
    has_conflict = await service.check_conflicts(doctor_id, date, time)
    return {"has_conflict": has_conflict}


@router.post("/bulk-reschedule", response_model=dict)
async def bulk_reschedule(
    doctor_id: str,
    old_date: str,
    new_date: str,
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Bulk reschedule appointments."""
    return await service.bulk_reschedule(doctor_id, old_date, new_date)


@router.get("/calendar/{doctor_id}", response_model=List[AppointmentResponse])
async def get_calendar(
    doctor_id: str,
    start_date: str,
    end_date: str,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Calendar view of appointments."""
    return await service.get_calendar_view(doctor_id, start_date, end_date)


@router.put("/{id}/notes", response_model=dict)
async def add_notes(
    id: str,
    notes: str,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Add appointment notes."""
    return await service.add_notes(id, notes)


@router.get("/upcoming-notifications", response_model=List[AppointmentResponse])
async def get_upcoming_notifications(
    current_user: dict = Depends(get_current_doctor_or_admin),
    service: AppointmentService = Depends(get_appointment_service),
):
    """Upcoming appointment alerts."""
    return await service.get_upcoming_notifications()
