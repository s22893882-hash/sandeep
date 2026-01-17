"""Appointment management API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth import get_current_user
from app.models.appointment import (
    AppointmentBookRequest,
    AppointmentResponse,
    AppointmentListResponse,
    AppointmentUpdateRequest,
    AppointmentCancellationRequest,
    AppointmentRescheduleRequest,
)
from app.services.appointment_service import AppointmentService
from app.database import db as database

router = APIRouter(prefix="/api/appointments", tags=["appointments"])
limiter = Limiter(key_func=get_remote_address)


def get_appointment_service() -> AppointmentService:
    """Get appointment service instance."""
    return AppointmentService(database.get_db())


@router.post("/book", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/15minutes")
async def book_appointment(
    request: Request,  # pylint: disable=unused-argument
    appointment_data: AppointmentBookRequest,
    current_user: dict = Depends(get_current_user),  # pylint: disable=unused-argument
    service: AppointmentService = Depends(get_appointment_service),
):
    """
    Book a new appointment.

    Creates a new appointment with conflict detection and availability checking.
    Rate limited to 5 requests per 15 minutes.
    """
    try:
        result = await service.book_appointment(
            patient_id=appointment_data.patient_id,
            doctor_id=appointment_data.doctor_id,
            appointment_date=appointment_data.appointment_date,
            appointment_time=appointment_data.appointment_time,
            reason=appointment_data.reason,
            notes=appointment_data.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("", response_model=AppointmentListResponse)
async def list_appointments(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """
    List patient appointments.

    Returns appointments for the authenticated user with optional status filtering.
    Supports pagination with limit and offset parameters.
    """
    try:
        patient = await database.get_db().patients.find_one({"user_id": current_user["user_id"]})
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found",
            )

        result = await service.get_patient_appointments(
            patient_id=patient["patient_id"],
            status=status_filter,
            limit=limit,
            offset=offset,
        )

        appointments = [AppointmentResponse(**apt) for apt in result["appointments"]]

        return AppointmentListResponse(
            appointments=appointments,
            total=result["total"],
            limit=result["limit"],
            offset=result["offset"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment_details(
    appointment_id: str,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """
    Get appointment details.

    Returns detailed information about a specific appointment.
    Patients can only view their own appointments.
    Doctors can view appointments assigned to them.
    Admins can view all appointments.
    """
    appointment = await service.get_appointment(
        appointment_id=appointment_id,
        user_id=current_user["user_id"],
        user_role=current_user.get("role", "patient"),
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found or access denied",
        )

    return AppointmentResponse(**appointment)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    update_data: AppointmentUpdateRequest,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """
    Update appointment.

    Allows updating notes and rescheduling appointments.
    Validates new time slots for availability.
    Cannot update completed or cancelled appointments.
    """
    appointment = await service.get_appointment(
        appointment_id=appointment_id,
        user_id=current_user["user_id"],
        user_role=current_user.get("role", "patient"),
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found or access denied",
        )

    try:
        updated = await service.update_appointment(appointment_id, update_data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )
        return AppointmentResponse(**updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/{appointment_id}", response_model=dict)
async def cancel_appointment(
    appointment_id: str,
    cancellation_data: AppointmentCancellationRequest,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """
    Cancel appointment.

    Cancels a pending or confirmed appointment.
    Cannot cancel completed or already cancelled appointments.
    """
    appointment = await service.get_appointment(
        appointment_id=appointment_id,
        user_id=current_user["user_id"],
        user_role=current_user.get("role", "patient"),
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found or access denied",
        )

    try:
        result = await service.cancel_appointment(
            appointment_id=appointment_id,
            cancellation_reason=cancellation_data.cancellation_reason,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{patient_id}/history", response_model=AppointmentListResponse)
async def get_appointment_history(
    patient_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """
    Get appointment history for patient.

    Returns all past and upcoming appointments sorted by date.
    Supports pagination.
    """
    patient = await database.get_db().patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found",
        )

    if patient["patient_id"] != patient_id and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await service.get_appointment_history(
        patient_id=patient_id,
        limit=limit,
        offset=offset,
    )

    appointments = [AppointmentResponse(**apt) for apt in result["appointments"]]

    return AppointmentListResponse(
        appointments=appointments,
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.put("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: str,
    reschedule_data: AppointmentRescheduleRequest,
    current_user: dict = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    """
    Reschedule appointment.

    Moves appointment to a new date and time.
    Validates availability at the new time slot.
    """
    appointment = await service.get_appointment(
        appointment_id=appointment_id,
        user_id=current_user["user_id"],
        user_role=current_user.get("role", "patient"),
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found or access denied",
        )

    try:
        updated = await service.reschedule_appointment(
            appointment_id=appointment_id,
            new_date=reschedule_data.new_appointment_date,
            new_time=reschedule_data.new_appointment_time,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )
        return AppointmentResponse(**updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
