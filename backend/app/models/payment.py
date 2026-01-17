"""
Payment-related Pydantic models for Phase 3 Module 3.
Complete payment processing system with Stripe integration ready.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    """Payment status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    """Payment method enum."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    INSURANCE = "insurance"
    WALLET = "wallet"
    CASH = "cash"


class Currency(str, Enum):
    """Currency enum."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"


class RefundStatus(str, Enum):
    """Refund status enum."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Core Payment Models


class PaymentCreate(BaseModel):
    """Model for creating a payment."""
    consultation_id: str = Field(..., description="Associated consultation ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: Currency = Field(default=Currency.USD, description="Payment currency")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")
    insurance_id: Optional[str] = Field(None, description="Insurance policy ID")
    description: Optional[str] = Field(None, description="Payment description")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional payment metadata")


class PaymentResponse(BaseModel):
    """Payment response model."""
    payment_id: str
    consultation_id: str
    amount: float
    currency: Currency
    payment_method: PaymentMethod
    payment_method_id: Optional[str]
    status: PaymentStatus
    stripe_payment_intent_id: Optional[str]
    stripe_charge_id: Optional[str]
    insurance_coverage: Optional[float]
    patient_amount: float
    description: Optional[str]
    metadata: dict
    created_at: datetime
    updated_at: datetime


class PaymentUpdate(BaseModel):
    """Model for updating payment."""
    status: Optional[PaymentStatus] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    insurance_coverage: Optional[float] = None
    patient_amount: Optional[float] = None


# Payment Intent Models (Stripe Integration)


class PaymentIntentCreate(BaseModel):
    """Model for creating Stripe payment intent."""
    amount: int = Field(..., gt=0, description="Amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    consultation_id: str = Field(..., description="Associated consultation ID")
    patient_id: str = Field(..., description="Patient user ID")
    doctor_id: str = Field(..., description="Doctor user ID")
    description: Optional[str] = Field(None, description="Payment description")
    metadata: Optional[dict] = Field(default_factory=dict, description="Payment metadata")


class PaymentIntentResponse(BaseModel):
    """Stripe payment intent response model."""
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str
    status: str


# Payment History Models


class PaymentHistoryResponse(BaseModel):
    """Payment history response model."""
    payment_id: str
    consultation_id: str
    amount: float
    currency: Currency
    payment_method: PaymentMethod
    status: PaymentStatus
    description: Optional[str]
    created_at: datetime
    consultation_date: Optional[datetime]
    doctor_name: Optional[str]


class PaymentHistoryQuery(BaseModel):
    """Model for querying payment history."""
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None
    consultation_id: Optional[str] = None
    status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# Receipt Models


class ReceiptResponse(BaseModel):
    """Payment receipt model."""
    receipt_id: str
    payment_id: str
    consultation_id: str
    patient_info: dict
    doctor_info: dict
    consultation_details: dict
    payment_breakdown: dict
    total_amount: float
    currency: Currency
    payment_method: PaymentMethod
    transaction_date: datetime
    receipt_url: Optional[str]
    invoice_number: str


# Refund Models


class RefundCreate(BaseModel):
    """Model for creating a refund."""
    payment_id: str = Field(..., description="Payment ID to refund")
    amount: Optional[float] = Field(None, gt=0, description="Refund amount (partial refund)")
    reason: str = Field(..., description="Refund reason")
    refund_method: str = Field(default="original", description="Refund method")
    metadata: Optional[dict] = Field(default_factory=dict, description="Refund metadata")


class RefundResponse(BaseModel):
    """Refund response model."""
    refund_id: str
    payment_id: str
    amount: float
    currency: Currency
    status: RefundStatus
    stripe_refund_id: Optional[str]
    reason: str
    refunded_at: Optional[datetime]
    created_at: datetime


# Insurance Models


class InsuranceVerification(BaseModel):
    """Model for insurance verification."""
    insurance_id: str = Field(..., description="Insurance policy ID")
    consultation_type: str = Field(..., description="Type of consultation")
    provider_name: str = Field(..., description="Insurance provider")
    coverage_percentage: float = Field(..., ge=0, le=100, description="Coverage percentage")
    deductible_amount: float = Field(default=0, ge=0, description="Deductible amount")
    copay_amount: Optional[float] = Field(None, ge=0, description="Copay amount")
    is_verified: bool = Field(default=False, description="Insurance verification status")
    verification_date: Optional[datetime]
    expiry_date: Optional[datetime]


class InsuranceClaim(BaseModel):
    """Model for insurance claim submission."""
    payment_id: str = Field(..., description="Associated payment ID")
    insurance_id: str = Field(..., description="Insurance policy ID")
    consultation_code: str = Field(..., description="Medical consultation code")
    diagnosis_codes: List[str] = Field(..., description="ICD-10 diagnosis codes")
    procedure_codes: List[str] = Field(..., description="CPT procedure codes")
    claim_amount: float = Field(..., gt=0, description="Claim amount")
    submission_date: datetime = Field(default_factory=datetime.utcnow)


class InsuranceClaimResponse(BaseModel):
    """Insurance claim response model."""
    claim_id: str
    payment_id: str
    insurance_id: str
    claim_amount: float
    approved_amount: Optional[float]
    status: str
    submission_date: datetime
    processing_date: Optional[datetime]
    settlement_date: Optional[datetime]


# Subscription Models


class SubscriptionCreate(BaseModel):
    """Model for creating follow-up subscription."""
    patient_id: str = Field(..., description="Patient user ID")
    doctor_id: str = Field(..., description="Doctor user ID")
    subscription_type: str = Field(..., description="Type of subscription")
    consultation_count: int = Field(default=5, ge=1, description="Number of consultations")
    duration_months: int = Field(default=3, ge=1, description="Subscription duration in months")
    discount_percentage: float = Field(default=10.0, ge=0, le=50, description="Subscription discount")


class SubscriptionResponse(BaseModel):
    """Subscription response model."""
    subscription_id: str
    patient_id: str
    doctor_id: str
    subscription_type: str
    consultation_count: int
    remaining_consultations: int
    duration_months: int
    discount_percentage: float
    total_amount: float
    discounted_amount: float
    status: str
    start_date: datetime
    end_date: datetime
    created_at: datetime


# Payment Analytics Models


class PaymentAnalytics(BaseModel):
    """Payment analytics model."""
    total_revenue: float
    total_payments: int
    successful_payments: int
    failed_payments: int
    refunded_amount: float
    average_transaction_amount: float
    payment_method_breakdown: dict
    monthly_revenue: List[dict]
    consultation_revenue: List[dict]


class DoctorEarnings(BaseModel):
    """Doctor earnings model."""
    doctor_id: str
    total_earnings: float
    total_consultations: int
    average_fee: float
    platform_fee: float
    net_earnings: float
    payment_period: dict
    earnings_breakdown: List[dict]


# Payment Configuration Models


class PaymentSettings(BaseModel):
    """Payment settings model."""
    platform_fee_percentage: float = Field(default=15.0, ge=0, le=30, description="Platform fee percentage")
    minimum_consultation_fee: float = Field(default=50.0, ge=0, description="Minimum consultation fee")
    maximum_consultation_fee: float = Field(default=500.0, ge=0, description="Maximum consultation fee")
    default_consultation_fee: float = Field(default=100.0, ge=0, description="Default consultation fee")
    currency: Currency = Field(default=Currency.USD, description="Default currency")
    supported_payment_methods: List[PaymentMethod] = Field(default_factory=lambda: [PaymentMethod.CREDIT_CARD, PaymentMethod.INSURANCE])
    auto_refund_enabled: bool = Field(default=False, description="Enable automatic refunds")
    refund_window_hours: int = Field(default=24, ge=1, le=168, description="Refund window in hours")


class PaymentWebhookEvent(BaseModel):
    """Payment webhook event model."""
    event_type: str
    event_id: str
    payment_intent_id: Optional[str]
    charge_id: Optional[str]
    amount: Optional[int]
    currency: Optional[str]
    status: Optional[str]
    metadata: dict
    created: datetime