"""Admin API endpoints for doctor management."""

from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import get_current_admin
from app.schemas.doctors import VerificationRequest
from app.services.doctor_service import DoctorService

router = APIRouter()


def get_doctor_service():
    """Dependency injection for DoctorService."""
    return DoctorService()


@router.patch("/doctors/{doctor_id}/verify", response_model=dict)
async def verify_doctor(
    doctor_id: str,
    verification_data: VerificationRequest,
    current_admin=Depends(get_current_admin),
    doctor_service: DoctorService = Depends(get_doctor_service),
):
    """
    Verify or reject a doctor's profile (admin only).

    - Requires: admin role
    - Updates is_verified flag and sends notification

    Args:
        doctor_id: Doctor document ID
        verification_data: Verification decision with optional rejection reason
        current_admin: Currently authenticated admin user
        doctor_service: Doctor service instance

    Returns:
        dict: Success message
    """
    try:
        result = await doctor_service.verify_doctor(doctor_id, verification_data.verified, verification_data.rejection_reason)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception 
        raise HTTPException(status_code=500, detail="Internal server error")
