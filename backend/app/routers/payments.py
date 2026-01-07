"""Payment management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.auth import get_current_user, get_current_admin
from app.models.payment import (
    PaymentCreate,
    PaymentResponse,
)
from app.services.payment_service import PaymentService
from app.database import get_database

router = APIRouter(prefix="/api/payments", tags=["payments"])


def get_payment_service(db=Depends(get_database)) -> PaymentService:
    """Get payment service instance."""
    return PaymentService(db)


@router.post("/initialize", response_model=PaymentResponse)
async def initialize_payment(
    data: PaymentCreate,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Create payment session."""
    return await service.initialize_payment(data)


@router.post("/process", response_model=dict)
async def process_payment(
    payment_id: str,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Process payment (Stripe/Razorpay)."""
    try:
        return await service.process_payment(payment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{id}/status", response_model=dict)
async def get_status(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Check payment status."""
    try:
        return await service.get_payment_status(id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/refund", response_model=dict)
async def refund(
    id: str,
    amount: float,
    reason: str,
    current_user: dict = Depends(get_current_admin),
    service: PaymentService = Depends(get_payment_service),
):
    """Issue refund."""
    try:
        return await service.refund_payment(id, amount, reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/invoices", response_model=List[dict])
async def get_invoices(
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get patient's invoices."""
    return await service.get_patient_invoices(current_user["user_id"])


@router.get("/invoices/{id}", response_model=dict)
async def get_invoice(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get invoice details."""
    try:
        return await service.get_invoice_details(id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/invoices/{id}/download", response_model=dict)
async def download_invoice(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Download invoice PDF (mock)."""
    return {"download_url": f"https://api.federatedhealth.ai/invoices/{id}.pdf"}


@router.get("/billing-history", response_model=List[dict])
async def get_billing_history(
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Complete billing history."""
    return await service.get_billing_history(current_user["user_id"])


@router.post("/subscription/create", response_model=dict)
async def create_subscription(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Create subscription plan."""
    return await service.create_subscription(current_user["user_id"], plan_id)


@router.put("/subscription/{id}/update", response_model=dict)
async def update_subscription(
    id: str,
    update_data: dict,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Update subscription."""
    return await service.update_subscription(id, update_data)


@router.post("/subscription/{id}/cancel", response_model=dict)
async def cancel_subscription(
    id: str,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Cancel subscription."""
    return await service.cancel_subscription(id)


@router.get("/transaction-logs", response_model=List[dict])
async def get_transaction_logs(
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Complete transaction logs."""
    return await service.get_transaction_logs(current_user["user_id"])
