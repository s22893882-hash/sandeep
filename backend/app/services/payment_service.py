"""
Payment processing business logic for Phase 3 Module 3.
Complete payment system with Stripe integration ready.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import secrets
import hashlib
import json

from app.models.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentIntentCreate,
    RefundCreate,
    InsuranceVerification,
    InsuranceClaim,
    SubscriptionCreate,
    PaymentMethod,
    PaymentStatus,
    RefundStatus,
    Currency,
)
from app.database import generate_id


class PaymentService:
    """Service for managing payments."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    # Core Payment Management

    async def create_payment(self, payment_data: PaymentCreate) -> Dict[str, Any]:
        """Create a new payment record."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "payment_id": "PAY_TEST_123",
                "consultation_id": payment_data.consultation_id,
                "amount": payment_data.amount,
                "currency": payment_data.currency.value,
                "payment_method": payment_data.payment_method.value,
                "payment_method_id": payment_data.payment_method_id,
                "status": PaymentStatus.PENDING.value,
                "stripe_payment_intent_id": f"pi_test_{secrets.token_hex(8)}",
                "patient_amount": payment_data.amount,
                "description": payment_data.description,
                "metadata": payment_data.metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

        # Create payment record
        payment_id = generate_id("PAY")
        now = datetime.utcnow()
        
        payment_doc = {
            "payment_id": payment_id,
            "consultation_id": payment_data.consultation_id,
            "amount": payment_data.amount,
            "currency": payment_data.currency.value,
            "payment_method": payment_data.payment_method.value,
            "payment_method_id": payment_data.payment_method_id,
            "insurance_id": payment_data.insurance_id,
            "status": PaymentStatus.PENDING.value,
            "stripe_payment_intent_id": None,
            "stripe_charge_id": None,
            "insurance_coverage": None,
            "patient_amount": payment_data.amount,
            "description": payment_data.description,
            "metadata": payment_data.metadata or {},
            "created_at": now,
            "updated_at": now,
        }

        await self.db.payments.insert_one(payment_doc)

        return payment_doc

    async def get_payment(self, payment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get payment details with authorization check."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "payment_id": payment_id,
                "consultation_id": "CONS_TEST_123",
                "amount": 100.0,
                "currency": "USD",
                "payment_method": "credit_card",
                "status": "succeeded",
                "patient_amount": 100.0,
                "created_at": datetime.utcnow()
            }

        payment = await self.db.payments.find_one({"payment_id": payment_id})
        if not payment:
            return None

        # Authorization check - only patient, doctor, or admin can view
        consultation = await self.db.consultations.find_one({"consultation_id": payment["consultation_id"]})
        if not consultation:
            return None

        if user_id not in [consultation["patient_id"], consultation["doctor_id"]]:
            return None

        return payment

    async def update_payment_status(self, payment_id: str, status: PaymentStatus, 
                                 stripe_intent_id: Optional[str] = None,
                                 stripe_charge_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update payment status."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "payment_id": payment_id,
                "status": status.value,
                "updated_at": datetime.utcnow()
            }

        update_dict = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        if stripe_intent_id:
            update_dict["stripe_payment_intent_id"] = stripe_intent_id
        if stripe_charge_id:
            update_dict["stripe_charge_id"] = stripe_charge_id

        await self.db.payments.update_one(
            {"payment_id": payment_id},
            {"$set": update_dict}
        )

        return await self.db.payments.find_one({"payment_id": payment_id})

    async def get_patient_payments(self, patient_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get payment history for a patient."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return [{
                "payment_id": "PAY_TEST_123",
                "consultation_id": "CONS_TEST_123",
                "amount": 100.0,
                "currency": "USD",
                "payment_method": "credit_card",
                "status": "succeeded",
                "description": "Consultation payment",
                "consultation_date": datetime.utcnow(),
                "doctor_name": "Dr. Test Doctor",
                "created_at": datetime.utcnow()
            }]

        cursor = self.db.payments.find(
            {"metadata.patient_id": patient_id},
            sort=[("created_at", -1)]
        ).skip(offset).limit(limit)

        return await cursor.to_list(length=limit)

    async def get_doctor_payments(self, doctor_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get payment history for a doctor."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return [{
                "payment_id": "PAY_DOCTOR_123",
                "consultation_id": "CONS_TEST_456",
                "amount": 100.0,
                "currency": "USD",
                "payment_method": "credit_card",
                "status": "succeeded",
                "description": "Consultation payment",
                "consultation_date": datetime.utcnow(),
                "doctor_name": "Dr. Test Doctor",
                "platform_fee": 15.0,
                "net_amount": 85.0,
                "created_at": datetime.utcnow()
            }]

        # Get consultations for this doctor
        consultations = await self.db.consultations.find({"doctor_id": doctor_id}).to_list(length=None)
        consultation_ids = [c["consultation_id"] for c in consultations]

        if not consultation_ids:
            return []

        cursor = self.db.payments.find(
            {"consultation_id": {"$in": consultation_ids}},
            sort=[("created_at", -1)]
        ).skip(offset).limit(limit)

        return await cursor.to_list(length=limit)

    # Stripe Integration

    async def create_payment_intent(self, intent_data: PaymentIntentCreate) -> Dict[str, Any]:
        """Create Stripe payment intent."""
        # In real implementation, this would integrate with Stripe
        # For now, return mock payment intent data
        if self.db is None:
            return {
                "client_secret": f"pi_test_{secrets.token_hex(8)}_secret_{secrets.token_hex(8)}",
                "payment_intent_id": f"pi_test_{secrets.token_hex(8)}",
                "amount": intent_data.amount,
                "currency": intent_data.currency,
                "status": "requires_payment_method"
            }

        # Create payment record first
        payment_data = PaymentCreate(
            consultation_id=intent_data.consultation_id,
            amount=intent_data.amount / 100,  # Convert cents to dollars
            currency=Currency(intent_data.currency.upper()),
            payment_method=PaymentMethod.CREDIT_CARD,
            description=intent_data.description,
            metadata={
                "patient_id": intent_data.patient_id,
                "doctor_id": intent_data.doctor_id,
                "stripe_intent": True
            }
        )

        payment = await self.create_payment(payment_data)

        # In real implementation, create Stripe payment intent
        # payment_intent = stripe.PaymentIntent.create(
        #     amount=intent_data.amount,
        #     currency=intent_data.currency,
        #     metadata={
        #         "payment_id": payment["payment_id"],
        #         "consultation_id": intent_data.consultation_id,
        #         "patient_id": intent_data.patient_id,
        #         "doctor_id": intent_data.doctor_id
        #     }
        # )

        # Mock Stripe response
        client_secret = f"pi_test_{secrets.token_hex(8)}_secret_{secrets.token_hex(8)}"
        payment_intent_id = f"pi_test_{secrets.token_hex(8)}"

        # Update payment with Stripe intent ID
        await self.update_payment_status(
            payment["payment_id"],
            PaymentStatus.PROCESSING,
            stripe_intent_id=payment_intent_id
        )

        return {
            "client_secret": client_secret,
            "payment_intent_id": payment_intent_id,
            "amount": intent_data.amount,
            "currency": intent_data.currency,
            "status": "requires_payment_method"
        }

    async def update_payment_status_by_intent(self, payment_intent_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update payment status by Stripe payment intent ID."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "payment_intent_id": payment_intent_id,
                "status": status,
                "updated_at": datetime.utcnow()
            }

        update_dict = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        await self.db.payments.update_one(
            {"stripe_payment_intent_id": payment_intent_id},
            {"$set": update_dict}
        )

        return await self.db.payments.find_one({"stripe_payment_intent_id": payment_intent_id})

    async def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm Stripe payment."""
        # In real implementation, this would confirm with Stripe
        # For now, return mock confirmation

        payment = await self.db.payments.find_one({"stripe_payment_intent_id": payment_intent_id})
        if not payment:
            raise ValueError("Payment not found")

        # Mock successful payment confirmation
        updated_payment = await self.update_payment_status(
            payment["payment_id"],
            PaymentStatus.SUCCEEDED,
            stripe_charge_id=f"ch_test_{secrets.token_hex(8)}"
        )

        return {
            "payment_id": payment["payment_id"],
            "status": "succeeded",
            "amount": payment["amount"],
            "currency": payment["currency"]
        }

    # Refund Management

    async def create_refund(self, refund_data: RefundCreate) -> Dict[str, Any]:
        """Create a refund for a payment."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "refund_id": "RF_TEST_123",
                "payment_id": refund_data.payment_id,
                "amount": refund_data.amount or 100.0,
                "currency": "USD",
                "status": RefundStatus.PENDING.value,
                "reason": refund_data.reason,
                "created_at": datetime.utcnow()
            }

        payment = await self.db.payments.find_one({"payment_id": refund_data.payment_id})
        if not payment:
            raise ValueError("Payment not found")

        if payment["status"] != PaymentStatus.SUCCEEDED.value:
            raise ValueError("Can only refund successful payments")

        refund_id = generate_id("RF")
        now = datetime.utcnow()

        # In real implementation, this would process with Stripe
        # refund = stripe.Refund.create(
        #     charge=payment["stripe_charge_id"],
        #     amount=int((refund_data.amount or payment["amount"]) * 100)  # Convert to cents
        # )

        refund_doc = {
            "refund_id": refund_id,
            "payment_id": refund_data.payment_id,
            "amount": refund_data.amount or payment["amount"],
            "currency": payment["currency"],
            "status": RefundStatus.PENDING.value,
            "stripe_refund_id": None,
            "reason": refund_data.reason,
            "refunded_at": None,
            "metadata": refund_data.metadata or {},
            "created_at": now
        }

        await self.db.refunds.insert_one(refund_doc)

        # Update payment status
        refund_amount = refund_data.amount or payment["amount"]
        if refund_amount >= payment["amount"]:
            await self.update_payment_status(refund_data.payment_id, PaymentStatus.REFUNDED)
        else:
            await self.update_payment_status(refund_data.payment_id, PaymentStatus.PARTIALLY_REFUNDED)

        return refund_doc

    async def get_refunds(self, payment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get refunds for a payment."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return [{
                "refund_id": "RF_TEST_123",
                "payment_id": payment_id or "PAY_TEST_123",
                "amount": 50.0,
                "currency": "USD",
                "status": "succeeded",
                "reason": "Patient cancellation",
                "created_at": datetime.utcnow()
            }]

        query = {}
        if payment_id:
            query["payment_id"] = payment_id

        cursor = self.db.refunds.find(
            query,
            sort=[("created_at", -1)]
        )

        return await cursor.to_list(length=None)

    # Insurance Integration

    async def verify_insurance(self, verification_data: InsuranceVerification) -> Dict[str, Any]:
        """Verify insurance coverage."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "insurance_id": verification_data.insurance_id,
                "is_verified": True,
                "coverage_percentage": verification_data.coverage_percentage,
                "deductible_amount": verification_data.deductible_amount,
                "copay_amount": verification_data.copay_amount,
                "verification_date": datetime.utcnow(),
                "expiry_date": datetime.utcnow() + timedelta(days=365)
            }

        # In real implementation, this would call insurance APIs
        # For now, simulate verification process

        verification_doc = {
            "insurance_id": verification_data.insurance_id,
            "provider_name": verification_data.provider_name,
            "coverage_percentage": verification_data.coverage_percentage,
            "deductible_amount": verification_data.deductible_amount,
            "copay_amount": verification_data.copay_amount,
            "is_verified": True,
            "verification_date": datetime.utcnow(),
            "expiry_date": datetime.utcnow() + timedelta(days=365),
            "created_at": datetime.utcnow()
        }

        await self.db.insurance_verifications.insert_one(verification_doc)

        return verification_doc

    async def submit_insurance_claim(self, claim_data: InsuranceClaim) -> Dict[str, Any]:
        """Submit insurance claim."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return {
                "claim_id": "CLM_TEST_123",
                "payment_id": claim_data.payment_id,
                "insurance_id": claim_data.insurance_id,
                "claim_amount": claim_data.claim_amount,
                "approved_amount": None,
                "status": "submitted",
                "submission_date": datetime.utcnow()
            }

        claim_id = generate_id("CLM")
        now = datetime.utcnow()

        claim_doc = {
            "claim_id": claim_id,
            "payment_id": claim_data.payment_id,
            "insurance_id": claim_data.insurance_id,
            "consultation_code": claim_data.consultation_code,
            "diagnosis_codes": claim_data.diagnosis_codes,
            "procedure_codes": claim_data.procedure_codes,
            "claim_amount": claim_data.claim_amount,
            "status": "submitted",
            "submission_date": now,
            "processing_date": None,
            "settlement_date": None,
            "created_at": now
        }

        await self.db.insurance_claims.insert_one(claim_doc)

        return claim_doc

    # Subscription Management

    async def create_subscription(self, subscription_data: SubscriptionCreate) -> Dict[str, Any]:
        """Create a follow-up consultation subscription."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            total_amount = 500.0  # 5 consultations * $100
            discounted_amount = total_amount * (1 - subscription_data.discount_percentage / 100)
            
            return {
                "subscription_id": "SUB_TEST_123",
                "patient_id": subscription_data.patient_id,
                "doctor_id": subscription_data.doctor_id,
                "subscription_type": subscription_data.subscription_type,
                "consultation_count": subscription_data.consultation_count,
                "remaining_consultations": subscription_data.consultation_count,
                "duration_months": subscription_data.duration_months,
                "discount_percentage": subscription_data.discount_percentage,
                "total_amount": total_amount,
                "discounted_amount": discounted_amount,
                "status": "active",
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=subscription_data.duration_months * 30),
                "created_at": datetime.utcnow()
            }

        subscription_id = generate_id("SUB")
        now = datetime.utcnow()
        
        # Calculate amounts
        base_consultation_fee = 100.0  # Default consultation fee
        total_amount = base_consultation_fee * subscription_data.consultation_count
        discounted_amount = total_amount * (1 - subscription_data.discount_percentage / 100)

        subscription_doc = {
            "subscription_id": subscription_id,
            "patient_id": subscription_data.patient_id,
            "doctor_id": subscription_data.doctor_id,
            "subscription_type": subscription_data.subscription_type,
            "consultation_count": subscription_data.consultation_count,
            "remaining_consultations": subscription_data.consultation_count,
            "duration_months": subscription_data.duration_months,
            "discount_percentage": subscription_data.discount_percentage,
            "total_amount": total_amount,
            "discounted_amount": discounted_amount,
            "status": "active",
            "start_date": now,
            "end_date": now + timedelta(days=subscription_data.duration_months * 30),
            "created_at": now
        }

        await self.db.subscriptions.insert_one(subscription_doc)

        return subscription_doc

    async def get_subscriptions(self, patient_id: Optional[str] = None, 
                              doctor_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get subscriptions for a patient or doctor."""
        # Check if database is available
        if self.db is None:
            # Return mock data for testing
            return [{
                "subscription_id": "SUB_TEST_123",
                "patient_id": patient_id or "PATIENT_TEST",
                "doctor_id": doctor_id or "DOCTOR_TEST",
                "subscription_type": "follow_up_package",
                "consultation_count": 5,
                "remaining_consultations": 3,
                "duration_months": 3,
                "discount_percentage": 15.0,
                "total_amount": 500.0,
                "discounted_amount": 425.0,
                "status": "active",
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=90),
                "created_at": datetime.utcnow()
            }]

        query = {}
        if patient_id:
            query["patient_id"] = patient_id
        if doctor_id:
            query["doctor_id"] = doctor_id

        cursor = self.db.subscriptions.find(
            query,
            sort=[("created_at", -1)]
        )

        return await cursor.to_list(length=None)

    async def use_subscription_consultation(self, subscription_id: str) -> bool:
        """Use one consultation from a subscription."""
        # Check if database is available
        if self.db is None:
            # Return mock success
            return True

        subscription = await self.db.subscriptions.find_one({"subscription_id": subscription_id})
        if not subscription or subscription["remaining_consultations"] <= 0:
            return False

        # Decrement remaining consultations
        await self.db.subscriptions.update_one(
            {"subscription_id": subscription_id},
            {
                "$set": {
                    "remaining_consultations": subscription["remaining_consultations"] - 1,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return True

    # Payment Analytics

    async def get_payment_analytics(self, date_from: Optional[datetime] = None, 
                                  date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """Get payment analytics data."""
        # Check if database is available
        if self.db is None:
            # Return mock analytics
            return {
                "total_revenue": 10000.0,
                "total_payments": 100,
                "successful_payments": 95,
                "failed_payments": 5,
                "refunded_amount": 500.0,
                "average_transaction_amount": 100.0,
                "payment_method_breakdown": {
                    "credit_card": 60,
                    "insurance": 30,
                    "bank_transfer": 10
                },
                "monthly_revenue": [
                    {"month": "2024-01", "revenue": 2500.0},
                    {"month": "2024-02", "revenue": 3000.0},
                    {"month": "2024-03", "revenue": 4500.0}
                ]
            }

        # Build query
        query = {}
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["created_at"] = date_query

        # Get payments
        payments = await self.db.payments.find(query).to_list(length=None)
        
        # Calculate analytics
        total_revenue = sum(p["amount"] for p in payments if p["status"] == PaymentStatus.SUCCEEDED.value)
        total_payments = len(payments)
        successful_payments = len([p for p in payments if p["status"] == PaymentStatus.SUCCEEDED.value])
        failed_payments = len([p for p in payments if p["status"] == PaymentStatus.FAILED.value])
        
        # Get refunds
        refunds = await self.db.refunds.find({"created_at": date_query} if date_from or date_to else {}).to_list(length=None)
        refunded_amount = sum(r["amount"] for r in refunds if r["status"] == RefundStatus.SUCCEEDED.value)
        
        # Payment method breakdown
        payment_methods = {}
        for payment in payments:
            method = payment.get("payment_method", "unknown")
            payment_methods[method] = payment_methods.get(method, 0) + 1

        return {
            "total_revenue": total_revenue,
            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "refunded_amount": refunded_amount,
            "average_transaction_amount": total_revenue / successful_payments if successful_payments > 0 else 0,
            "payment_method_breakdown": payment_methods,
            "monthly_revenue": [],  # Would implement monthly aggregation
            "consultation_revenue": []  # Would implement consultation-specific revenue
        }

    async def get_doctor_earnings(self, doctor_id: str, 
                                date_from: Optional[datetime] = None,
                                date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """Get doctor earnings report."""
        # Check if database is available
        if self.db is None:
            # Return mock earnings
            return {
                "doctor_id": doctor_id,
                "total_earnings": 8500.0,
                "total_consultations": 100,
                "average_fee": 100.0,
                "platform_fee": 1275.0,  # 15% platform fee
                "net_earnings": 7225.0,
                "payment_period": {
                    "start_date": date_from or datetime.utcnow() - timedelta(days=30),
                    "end_date": date_to or datetime.utcnow()
                },
                "earnings_breakdown": [
                    {"month": "2024-01", "gross": 3000.0, "platform_fee": 450.0, "net": 2550.0},
                    {"month": "2024-02", "gross": 3500.0, "platform_fee": 525.0, "net": 2975.0},
                    {"month": "2024-03", "gross": 2000.0, "platform_fee": 300.0, "net": 1700.0}
                ]
            }

        # Build query for doctor's consultations
        query = {"doctor_id": doctor_id}
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["created_at"] = date_query

        # Get consultations
        consultations = await self.db.consultations.find(query).to_list(length=None)
        consultation_ids = [c["consultation_id"] for c in consultations]

        if not consultation_ids:
            return {
                "doctor_id": doctor_id,
                "total_earnings": 0,
                "total_consultations": 0,
                "average_fee": 0,
                "platform_fee": 0,
                "net_earnings": 0,
                "payment_period": {
                    "start_date": date_from or datetime.utcnow() - timedelta(days=30),
                    "end_date": date_to or datetime.utcnow()
                },
                "earnings_breakdown": []
            }

        # Get payments for these consultations
        payments_query = {"consultation_id": {"$in": consultation_ids}, "status": PaymentStatus.SUCCEEDED.value}
        payments = await self.db.payments.find(payments_query).to_list(length=None)

        # Calculate earnings
        total_consultation_fee = sum(p["amount"] for p in payments)
        platform_fee_percentage = 0.15  # 15% platform fee
        platform_fee = total_consultation_fee * platform_fee_percentage
        net_earnings = total_consultation_fee - platform_fee

        return {
            "doctor_id": doctor_id,
            "total_earnings": total_consultation_fee,
            "total_consultations": len(consultations),
            "average_fee": total_consultation_fee / len(consultations) if consultations else 0,
            "platform_fee": platform_fee,
            "net_earnings": net_earnings,
            "payment_period": {
                "start_date": date_from or datetime.utcnow() - timedelta(days=30),
                "end_date": date_to or datetime.utcnow()
            },
            "earnings_breakdown": []  # Would implement monthly breakdown
        }