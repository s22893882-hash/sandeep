"""Payment-related data models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    """Payment status levels."""

    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"


class InvoiceStatus(str, Enum):
    """Invoice status levels."""

    draft = "draft"
    issued = "issued"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"


class PaymentBase(BaseModel):
    """Base payment model."""

    patient_id: str
    doctor_id: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")
    payment_method: str


class PaymentCreate(PaymentBase):
    """Payment creation request model."""

    appointment_id: Optional[str] = None
    consultation_id: Optional[str] = None


class PaymentResponse(PaymentBase):
    """Payment response model."""

    payment_id: str
    status: PaymentStatus
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class Invoice(BaseModel):
    """Invoice model."""

    invoice_id: str
    patient_id: str
    invoice_number: str
    amount: float
    currency: str
    issued_date: datetime
    due_date: datetime
    status: InvoiceStatus
    payment_id: Optional[str] = None


class SubscriptionPlan(BaseModel):
    """Subscription plan model."""

    plan_id: str
    name: str
    amount: float
    currency: str
    interval: str  # monthly, yearly
    features: List[str]


class Subscription(BaseModel):
    """Subscription model."""

    subscription_id: str
    patient_id: str
    plan_id: str
    status: str
    start_date: datetime
    end_date: datetime
    auto_renewal: bool = True


class Refund(BaseModel):
    """Refund model."""

    refund_id: str
    payment_id: str
    amount: float
    reason: str
    status: str
    processed_date: Optional[datetime] = None
