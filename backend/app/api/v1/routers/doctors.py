"""
Doctor API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any
from app.core.security import create_access_token
from app.api.v1.dependencies.auth import get_current_user, get_current_active_doctor, get_current_admin
from app.schemas.doctors import (
    DoctorRegistrationRequest,
    DoctorProfileResponse,
    DoctorListResponse,
    WorkingHoursUpdate,
    AvailabilityStatusUpdate,
    VerificationRequest,
    AvailableSlot,
    DoctorStatistics,
    RatingResponse,
    AppointmentResponse,
    DoctorSearchFilters,
)
from app.services.doctor_service import DoctorService

router = APIRouter()


def get_doctor_service():
    """Dependency injection for DoctorService."""
    return DoctorService()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_doctor(
    registration_data: DoctorRegistrationRequest,
    current_user=Depends(get_current_user),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    Complete doctor registration/onboarding.

    - Requires: JWT authentication (user already registered)
    - Creates doctor profile and sets verification status to pending

    Args:
        registration_data: Doctor registration details
        current_user: Currently authenticated user
        doctor_service: Doctor service instance

    Returns:
        dict: Success message with doctor_id
    """
    try:
        result = await doctor_service.register_doctor(current_user["user_id"], registration_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{doctor_id}", response_model=DoctorProfileResponse)
async def get_doctor_profile(doctor_id: str, doctor_service: DoctorService = Depends(get_doctor_service)):
    """
    Get doctor profile by ID.

    - Public endpoint (optional JWT)
    - Returns full doctor profile with ratings

    Args:
        doctor_id: Doctor document ID
        doctor_service: Doctor service instance

    Returns:
        DoctorProfileResponse: Complete doctor profile
    """
    try:
        profile = await doctor_service.get_doctor_profile(doctor_id)
        return DoctorProfileResponse(**profile)
    except ValueError:
        raise HTTPException(status_code=404, detail="Doctor not found")
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=List[DoctorListResponse])
async def list_doctors(
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    rating_min: Optional[float] = Query(None, description="Minimum rating filter"),
    consultation_fee_max: Optional[float] = Query(None, description="Maximum fee filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    is_verified: Optional[bool] = Query(None, description="Verified only"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    List all doctors with filters (public endpoint).

    - Public endpoint
    - Supports multiple filters and pagination
    - Returns simplified doctor info

    Args:
        specialization: Filter by medical specialization
        rating_min: Minimum average rating
        consultation_fee_max: Maximum consultation fee
        location: Clinic location
        is_verified: Show only verified doctors
        limit: Number of results per page
        offset: Pagination offset
        doctor_service: Doctor service instance

    Returns:
        List[DoctorListResponse]: List of doctor profiles
    """
    try:
        doctors = await doctor_service.search_doctors(
            specialization=specialization,
            rating_min=rating_min,
            consultation_fee_max=consultation_fee_max,
            location=location,
            is_verified=is_verified,
            limit=limit,
            offset=offset,
        )
        return [DoctorListResponse(**doctor) for doctor in doctors]
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search", response_model=List[DoctorListResponse])
async def search_doctors(
    q: Optional[str] = Query(None, description="Search query (name/specialization)"),
    specialization: Optional[str] = Query(None),
    rating_min: Optional[float] = Query(None),
    consultation_fee_max: Optional[float] = Query(None),
    location: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    Search doctors with query and filters.

    - Public endpoint
    - Full-text search on name/specialization
    - Returns filtered and ranked results

    Args:
        q: Search query for name or specialization
        specialization: Specialization filter
        rating_min: Minimum rating filter
        consultation_fee_max: Maximum fee filter
        location: Location filter
        is_verified: Verified filter
        limit: Results limit
        offset: Pagination offset
        doctor_service: Doctor service instance

    Returns:
        List[DoctorListResponse]: Search results
    """
    try:
        doctors = await doctor_service.search_doctors(
            query=q,
            specialization=specialization,
            rating_min=rating_min,
            consultation_fee_max=consultation_fee_max,
            location=location,
            is_verified=is_verified,
            limit=limit,
            offset=offset,
        )
        return [DoctorListResponse(**doctor) for doctor in doctors]
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/me", response_model=DoctorProfileResponse)
async def update_doctor_profile(
    update_data: Dict[str, Any],
    current_doctor=Depends(get_current_active_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    Update own doctor profile.

    - Requires: doctor role and active profile
    - Can update most profile fields
    - License changes reset verification

    Args:
        update_data: Fields to update
        current_doctor: Currently authenticated doctor
        doctor_service: Doctor service instance

    Returns:
        DoctorProfileResponse: Updated profile
    """
    try:
        doctor_id = current_doctor["doctor_id"]
        profile = await doctor_service.update_doctor_profile(doctor_id, update_data)
        return DoctorProfileResponse(**profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me/appointments", response_model=List[AppointmentResponse])
async def get_doctor_appointments(
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    current_doctor=Depends(get_current_active_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    Get doctor's appointments.

    - Requires: doctor role
    - Filter by status and date range

    Args:
        status: Appointment status filter
        date_from: Start date filter
        date_to: End date filter
        limit: Results limit
        offset: Pagination offset
        current_doctor: Currently authenticated doctor
        doctor_service: Doctor service instance

    Returns:
        List[AppointmentResponse]: Appointment list
    """
    # This will be implemented when appointment service is available
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/me/statistics", response_model=DoctorStatistics)
async def get_doctor_statistics(
    current_doctor=Depends(get_current_active_doctor), doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Get doctor statistics and performance metrics.

    - Requires: doctor role
    - Returns performance data and analytics

    Args:
        current_doctor: Currently authenticated doctor
        doctor_service: Doctor service instance

    Returns:
        DoctorStatistics: Performance metrics
    """
    try:
        user_id = current_doctor.get("user_id", "")
        stats = await doctor_service.get_doctor_statistics(user_id)
        return DoctorStatistics(**stats)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception 
        print(f"Statistics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me/working-hours")
async def get_working_hours(
    current_doctor=Depends(get_current_active_doctor), doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Get doctor working hours.

    - Requires: doctor role
    - Returns weekly schedule

    Args:
        current_doctor: Currently authenticated doctor
        doctor_service: Doctor service instance

    Returns:
        dict: Working hours by day
    """
    try:
        doctor_id = current_doctor["doctor_id"]
        doctor = await doctor_service.get_doctor_profile(doctor_id)
        return {"working_hours": doctor["working_hours"], "is_available_weekends": doctor.get("is_available_weekends", False)}
    except ValueError:
        raise HTTPException(status_code=404, detail="Doctor not found")
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/me/working-hours", response_model=dict)
async def update_working_hours(
    working_hours_data: WorkingHoursUpdate,
    current_doctor=Depends(get_current_active_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    Update doctor working hours.

    - Requires: doctor role
    - Validates time format and logic

    Args:
        working_hours_data: New working hours
        current_doctor: Currently authenticated doctor
        doctor_service: Doctor service instance

    Returns:
        dict: Updated working hours
    """
    try:
        result = await doctor_service.update_working_hours(current_doctor["user_id"], working_hours_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/availability", response_model=dict)
async def update_availability_status(
    status_data: AvailabilityStatusUpdate,
    current_doctor=Depends(get_current_active_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    Update doctor availability status.

    - Requires: doctor role
    - Allows setting available/on-leave/unavailable

    Args:
        status_data: New availability status
        current_doctor: Currently authenticated doctor
        doctor_service: Doctor service instance

    Returns:
        dict: Updated status
    """
    try:
        result = await doctor_service.update_availability_status(current_doctor["user_id"], status_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{doctor_id}/specializations", response_model=List[Dict[str, str]])
async def get_doctor_specializations(doctor_id: str, doctor_service: DoctorService = Depends(get_doctor_service)):
    """
    Get doctor specializations.

    - Public endpoint

    Args:
        doctor_id: Doctor document ID
        doctor_service: Doctor service instance

    Returns:
        List[dict]: Specializations with expertise level
    """
    try:
        doctor = await doctor_service.get_doctor_profile(doctor_id)
        return [
            {"name": spec.specialization_name, "expertise_level": spec.expertise_level} for spec in doctor["specializations"]
        ]
    except ValueError:
        raise HTTPException(status_code=404, detail="Doctor not found")
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/me/specializations", response_model=List[Dict[str, str]], status_code=status.HTTP_201_CREATED)
async def add_specialization(
    specialization: Dict[str, str],
    current_doctor=Depends(get_current_active_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    Add specialization to doctor profile.

    - Requires: doctor role

    Args:
        specialization: New specialization details
        current_doctor: Currently authenticated doctor
        doctor_service: Doctor service instance

    Returns:
        List[dict]: Updated specializations
    """
    try:
        user_id = current_doctor["user_id"]

        # Get current doctor data
        doctor = await doctor_service.get_doctor_profile(current_doctor["doctor_id"])
        current_specializations = doctor["specializations"]

        # Add new specialization
        current_specializations.append(
            {
                "specialization_name": specialization["specialization_name"],
                "expertise_level": specialization["expertise_level"],
            }
        )

        # Update doctor profile
        result = await doctor_service.update_doctor_profile(user_id, {"specializations": current_specializations})

        return result["specializations"]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{doctor_id}/available-slots", response_model=List[AvailableSlot])
async def get_available_slots(
    doctor_id: str,
    date: datetime,
    duration_minutes: int = Query(30, ge=15, le=240),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    Get available appointment slots for a doctor on a specific date.

    - Public endpoint
    - Calculates free slots based on working hours and appointments

    Args:
        doctor_id: Doctor document ID
        date: Target date
        duration_minutes: Slot duration (default 30 min)
        doctor_service: Doctor service instance

    Returns:
        List[AvailableSlot]: Available time slots
    """
    try:
        slots = await doctor_service.get_available_slots(doctor_id, date, duration_minutes)
        return [AvailableSlot(**slot) for slot in slots]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{doctor_id}/ratings", response_model=RatingResponse)
async def get_doctor_ratings(
    doctor_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    Get doctor rating and reviews.

    - Public endpoint
    - Returns rating statistics and recent reviews

    Args:
        doctor_id: Doctor document ID
        limit: Reviews limit
        offset: Reviews offset
        doctor_service: Doctor service instance

    Returns:
        RatingResponse: Ratings and reviews
    """
    # This will be implemented when review service is available
    raise HTTPException(status_code=501, detail="Not implemented")
