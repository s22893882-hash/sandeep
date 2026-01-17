"""
Payment API endpoints for Phase 3 Module 3.
Complete payment processing system with Stripe integration ready.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime

from app.auth import get_current_user, security, TESTING_MODE
from app.models.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentUpdate,
    PaymentIntentCreate,
    PaymentIntentResponse,
    RefundCreate,
    RefundResponse,
    InsuranceVerification,
    InsuranceClaim,
    SubscriptionCreate,
    SubscriptionResponse,
    PaymentHistoryQuery,
    PaymentHistoryResponse,
    ReceiptResponse,
    PaymentAnalytics,
    DoctorEarnings,
    PaymentSettings,
    PaymentWebhookEvent,
)
from app.services.payment_service import PaymentService
from app.database import db as database

router = APIRouter(prefix="/api/payments", tags=["payments"])


def get_payment_service() -> PaymentService:
    """Get payment service instance."""
    return PaymentService(database.get_db())


async def optional_auth(
    credentials: HTTPAuthorizationCredentials = Depends(
        security if not TESTING_MODE else lambda: None
    ),
):
    """Optional authentication for testing."""
    if TESTING_MODE:
        # In test mode, return a mock user
        return {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "role": "patient",
            "user_type": "patient",
        }
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await get_current_user(credentials)


# 1. Core Payment Management (3 APIs)

@router.post("/create", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Create a new payment for consultation.
    
    Creates payment record and initializes payment processing.
    """
    try:
        result = await service.create_payment(payment_data)
        return {
            "payment_id": result["payment_id"],
            "status": result["status"],
            "amount": result["amount"],
            "currency": result["currency"],
            "client_secret": result.get("stripe_payment_intent_id")
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Get payment details.
    
    Returns payment information for authorized users.
    """
    payment = await service.get_payment(payment_id, current_user["user_id"])
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found or access denied",
        )
    return PaymentResponse(**payment)


@router.put("/{payment_id}/status", response_model=PaymentResponse)
async def update_payment_status(
    payment_id: str,
    update_data: PaymentUpdate,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Update payment status.
    
    Updates payment status (typically used by webhook handlers).
    """
    try:
        from app.models.payment import PaymentStatus
        payment = await service.update_payment_status(
            payment_id, 
            update_data.status or PaymentStatus.PROCESSING,
            update_data.stripe_payment_intent_id,
            update_data.stripe_charge_id
        )
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )
        return PaymentResponse(**payment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# 2. Stripe Integration (3 APIs)

@router.post("/intent", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_intent(
    intent_data: PaymentIntentCreate,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Create Stripe payment intent.
    
    Creates Stripe payment intent for consultation payment.
    """
    try:
        result = await service.create_payment_intent(intent_data)
        return PaymentIntentResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/confirm/{payment_intent_id}", response_model=dict)
async def confirm_payment(
    payment_intent_id: str,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Confirm Stripe payment.
    
    Confirms payment after Stripe payment method is attached.
    """
    try:
        result = await service.confirm_payment(payment_intent_id)
        return {
            "payment_id": result["payment_id"],
            "status": result["status"],
            "amount": result["amount"],
            "currency": result["currency"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/webhook", response_model=dict)
async def payment_webhook(
    request: Request,
    service: PaymentService = Depends(get_payment_service),
):
    """
    Stripe webhook handler.
    
    Handles Stripe webhook events for payment status updates.
    """
    try:
        # In real implementation, verify webhook signature
        event_data = await request.json()
        
        event_type = event_data.get("type")
        
        if event_type == "payment_intent.succeeded":
            payment_intent = event_data["data"]["object"]
            payment_intent_id = payment_intent["id"]
            
            # Confirm the payment
            result = await service.confirm_payment(payment_intent_id)
            
            return {"status": "processed", "payment_id": result["payment_id"]}
        
        elif event_type == "payment_intent.payment_failed":
            payment_intent = event_data["data"]["object"]
            payment_intent_id = payment_intent["id"]
            
            # Update payment status to failed
            await service.update_payment_status_by_intent(payment_intent_id, "failed")
            
            return {"status": "processed", "payment_intent_id": payment_intent_id}
        
        return {"status": "ignored", "event_type": event_type}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing error: {str(e)}",
        )


# 3. Payment History (2 APIs)

@router.get("/history/patient", response_model=List[PaymentHistoryResponse])
async def get_patient_payment_history(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Get patient payment history.
    
    Returns complete payment history for authenticated patient.
    """
    payments = await service.get_patient_payments(
        current_user["user_id"], limit, offset
    )
    return [PaymentHistoryResponse(**payment) for payment in payments]


@router.get("/history/doctor", response_model=List[PaymentHistoryResponse])
async def get_doctor_payment_history(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Get doctor payment history.
    
    Returns payment history for consultations conducted by doctor.
    """
    payments = await service.get_doctor_payments(
        current_user["user_id"], limit, offset
    )
    return [PaymentHistoryResponse(**payment) for payment in payments]


# 4. Receipt Management (1 API)

@router.get("/{payment_id}/receipt", response_model=ReceiptResponse)
async def get_payment_receipt(
    payment_id: str,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Get payment receipt.
    
    Returns detailed receipt for a payment.
    """
    payment = await service.get_payment(payment_id, current_user["user_id"])
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found or access denied",
        )
    
    # In real implementation, generate PDF receipt
    # For now, return mock receipt data
    receipt_data = {
        "receipt_id": f"REC_{payment_id}",
        "payment_id": payment_id,
        "consultation_id": payment["consultation_id"],
        "patient_info": {
            "id": current_user["user_id"],
            "name": "Test Patient"
        },
        "doctor_info": {
            "id": "DOCTOR_TEST",
            "name": "Dr. Test Doctor"
        },
        "consultation_details": {
            "date": payment["created_at"],
            "duration": "30 minutes",
            "type": "General Consultation"
        },
        "payment_breakdown": {
            "consultation_fee": payment["amount"],
            "platform_fee": 0,
            "insurance_coverage": 0,
            "patient_payment": payment["amount"]
        },
        "total_amount": payment["amount"],
        "currency": payment["currency"],
        "payment_method": payment["payment_method"],
        "transaction_date": payment["created_at"],
        "receipt_url": f"/receipts/{payment_id}.pdf",
        "invoice_number": f"INV-{payment_id[:8].upper()}"
    }
    
    return ReceiptResponse(**receipt_data)


# 5. Refund Management (3 APIs)

@router.post("/{payment_id}/refund", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
async def create_refund(
    payment_id: str,
    refund_data: RefundCreate,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Create refund for payment.
    
    Initiates refund process for a payment.
    """
    try:
        result = await service.create_refund(refund_data)
        return RefundResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{payment_id}/refunds", response_model=List[RefundResponse])
async def get_payment_refunds(
    payment_id: str,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Get refunds for payment.
    
    Returns all refunds associated with a payment.
    """
    refunds = await service.get_refunds(payment_id)
    return [RefundResponse(**refund) for refund in refunds]


@router.post("/{payment_id}/refund/auto", response_model=RefundResponse)
async def auto_refund_payment(
    payment_id: str,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Automatic refund for cancelled consultations.
    
    Initiates automatic refund for cancelled consultations within refund window.
    """
    try:
        refund_data = RefundCreate(
            payment_id=payment_id,
            reason="Automatic refund - consultation cancelled",
            metadata={"auto_refund": True}
        )
        
        result = await service.create_refund(refund_data)
        return RefundResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# 6. Insurance Integration (2 APIs)

@router.post("/insurance/verify", response_model=dict, status_code=status.HTTP_201_CREATED)
async def verify_insurance(
    verification_data: InsuranceVerification,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Verify insurance coverage.
    
    Verifies insurance policy and calculates coverage.
    """
    try:
        result = await service.verify_insurance(verification_data)
        return {
            "verification_id": result["insurance_id"],
            "is_verified": result["is_verified"],
            "coverage_percentage": result["coverage_percentage"],
            "deductible_amount": result["deductible_amount"],
            "copay_amount": result.get("copay_amount"),
            "verification_date": result["verification_date"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/insurance/claim", response_model=dict, status_code=status.HTTP_201_CREATED)
async def submit_insurance_claim(
    claim_data: InsuranceClaim,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Submit insurance claim.
    
    Submits insurance claim for reimbursement.
    """
    try:
        result = await service.submit_insurance_claim(claim_data)
        return {
            "claim_id": result["claim_id"],
            "status": result["status"],
            "submission_date": result["submission_date"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# 7. Subscription Management (3 APIs)

@router.post("/subscription", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Create consultation subscription.
    
    Creates subscription for multiple consultations with discount.
    """
    try:
        result = await service.create_subscription(subscription_data)
        return SubscriptionResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/subscription/patient", response_model=List[SubscriptionResponse])
async def get_patient_subscriptions(
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Get patient subscriptions.
    
    Returns all subscriptions for authenticated patient.
    """
    subscriptions = await service.get_subscriptions(patient_id=current_user["user_id"])
    return [SubscriptionResponse(**sub) for sub in subscriptions]


@router.get("/subscription/doctor", response_model=List[SubscriptionResponse])
async def get_doctor_subscriptions(
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Get doctor subscriptions.
    
    Returns all subscriptions for consultations with this doctor.
    """
    subscriptions = await service.get_subscriptions(doctor_id=current_user["user_id"])
    return [SubscriptionResponse(**sub) for sub in subscriptions]


# 8. Payment Analytics (2 APIs)

@router.get("/analytics/overview", response_model=PaymentAnalytics)
async def get_payment_analytics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Get payment analytics.
    
    Returns payment analytics for the platform or user.
    """
    # Only admin can view platform-wide analytics
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view platform analytics",
        )
    
    analytics = await service.get_payment_analytics(date_from, date_to)
    return PaymentAnalytics(**analytics)


@router.get("/analytics/doctor-earnings", response_model=DoctorEarnings)
async def get_doctor_earnings(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Get doctor earnings report.
    
    Returns detailed earnings report for doctor.
    """
    # Only doctor can view their own earnings
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can view earnings reports",
        )
    
    earnings = await service.get_doctor_earnings(
        current_user["user_id"], date_from, date_to
    )
    return DoctorEarnings(**earnings)


# 9. Payment Settings (1 API)

@router.get("/settings", response_model=PaymentSettings)
async def get_payment_settings(
    current_user: dict = Depends(optional_auth),
):
    """
    Get payment settings.
    
    Returns platform payment settings and configuration.
    """
    # Only admin can view payment settings
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view payment settings",
        )
    
    # Return default settings (in real implementation, fetch from database)
    settings = {
        "platform_fee_percentage": 15.0,
        "minimum_consultation_fee": 50.0,
        "maximum_consultation_fee": 500.0,
        "default_consultation_fee": 100.0,
        "currency": "USD",
        "supported_payment_methods": ["credit_card", "insurance"],
        "auto_refund_enabled": False,
        "refund_window_hours": 24
    }
    
    return PaymentSettings(**settings)


# Additional utility endpoints

@router.get("/stats/my-stats")
async def get_my_payment_stats(
    current_user: dict = Depends(optional_auth),
    service: PaymentService = Depends(get_payment_service),
):
    """
    Get payment statistics for current user.
    
    Returns basic payment statistics for patient or doctor.
    """
    user_id = current_user["user_id"]
    user_type = current_user.get("user_type", current_user.get("role"))
    
    if user_type == "patient":
        payments = await service.get_patient_payments(user_id, limit=100)
        total_spent = sum(p["amount"] for p in payments if p["status"] == "succeeded")
        successful_payments = len([p for p in payments if p["status"] == "succeeded"])
        
        return {
            "total_spent": total_spent,
            "successful_payments": successful_payments,
            "user_type": user_type,
            "message": "Patient payment statistics"
        }
    
    elif user_type == "doctor":
        earnings = await service.get_doctor_earnings(user_id)
        return {
            "total_earnings": earnings.get("total_earnings", 0),
            "net_earnings": earnings.get("net_earnings", 0),
            "total_consultations": earnings.get("total_consultations", 0),
            "user_type": user_type,
            "message": "Doctor earnings statistics"
        }
    
    return {
        "total_payments": 0,
        "user_type": user_type,
        "message": "Payment statistics"
    }