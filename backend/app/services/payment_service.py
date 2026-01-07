"""Payment management business logic."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.payment import (
    PaymentCreate,
    PaymentStatus,
    InvoiceStatus,
)
from app.database import generate_id, format_mongo_doc, format_mongo_docs


class PaymentService:
    """Service for managing payments."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def initialize_payment(self, data: PaymentCreate) -> Dict[str, Any]:
        """Create payment session."""
        payment_id = generate_id("PAY")
        payment_doc = {
            "payment_id": payment_id,
            "patient_id": data.patient_id,
            "doctor_id": data.doctor_id,
            "amount": data.amount,
            "currency": data.currency,
            "status": PaymentStatus.pending.value,
            "payment_method": data.payment_method,
            "appointment_id": data.appointment_id,
            "consultation_id": data.consultation_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await self.db.payments.insert_one(payment_doc)
        return format_mongo_doc(payment_doc)

    async def process_payment(self, payment_id: str) -> Dict[str, Any]:
        """Process payment (Stripe/Razorpay mock)."""
        payment = await self.db.payments.find_one({"payment_id": payment_id})
        if not payment:
            raise ValueError("Payment not found")

        transaction_id = generate_id("TXN")
        await self.db.payments.update_one(
            {"payment_id": payment_id},
            {
                "$set": {
                    "status": PaymentStatus.completed.value,
                    "transaction_id": transaction_id,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        # Create invoice automatically
        await self.create_invoice(payment_id)

        return {"payment_id": payment_id, "status": "completed", "transaction_id": transaction_id}

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Check payment status."""
        payment = await self.db.payments.find_one({"payment_id": payment_id})
        if not payment:
            raise ValueError("Payment not found")
        return {"payment_id": payment_id, "status": payment["status"]}

    async def refund_payment(self, payment_id: str, amount: float, reason: str) -> Dict[str, Any]:
        """Issue refund."""
        payment = await self.db.payments.find_one({"payment_id": payment_id})
        if not payment:
            raise ValueError("Payment not found")

        refund_id = generate_id("REF")
        refund_doc = {
            "refund_id": refund_id,
            "payment_id": payment_id,
            "amount": amount,
            "reason": reason,
            "status": "completed",
            "processed_date": datetime.utcnow(),
        }
        await self.db.refunds.insert_one(refund_doc)

        await self.db.payments.update_one(
            {"payment_id": payment_id}, {"$set": {"status": PaymentStatus.refunded.value, "updated_at": datetime.utcnow()}}
        )

        return refund_doc

    async def get_patient_invoices(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get patient's invoices."""
        cursor = self.db.invoices.find({"patient_id": patient_id}).sort("issued_date", -1)
        return await cursor.to_list(length=None)

    async def get_invoice_details(self, invoice_id: str) -> Dict[str, Any]:
        """Get invoice details."""
        invoice = await self.db.invoices.find_one({"invoice_id": invoice_id})
        if not invoice:
            raise ValueError("Invoice not found")
        return invoice

    async def create_invoice(self, payment_id: str) -> Dict[str, Any]:
        """Create invoice from payment."""
        payment = await self.db.payments.find_one({"payment_id": payment_id})
        invoice_id = generate_id("INV")
        invoice_doc = {
            "invoice_id": invoice_id,
            "patient_id": payment["patient_id"],
            "invoice_number": f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{invoice_id[-5:]}",
            "amount": payment["amount"],
            "currency": payment["currency"],
            "issued_date": datetime.utcnow(),
            "due_date": datetime.utcnow() + timedelta(days=30),
            "status": InvoiceStatus.paid.value,
            "payment_id": payment_id,
        }
        await self.db.invoices.insert_one(invoice_doc)
        return invoice_doc

    async def get_billing_history(self, patient_id: str) -> List[Dict[str, Any]]:
        """Complete billing history."""
        cursor = self.db.payments.find({"patient_id": patient_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def create_subscription(self, patient_id: str, plan_id: str) -> Dict[str, Any]:
        """Create subscription plan."""
        subscription_id = generate_id("SUB")
        now = datetime.utcnow()
        sub_doc = {
            "subscription_id": subscription_id,
            "patient_id": patient_id,
            "plan_id": plan_id,
            "status": "active",
            "start_date": now,
            "end_date": now + timedelta(days=30),
            "auto_renewal": True,
        }
        await self.db.subscriptions.insert_one(sub_doc)
        return sub_doc

    async def update_subscription(self, subscription_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update subscription."""
        await self.db.subscriptions.update_one({"subscription_id": subscription_id}, {"$set": update_data})
        return await self.db.subscriptions.find_one({"subscription_id": subscription_id})

    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel subscription."""
        await self.db.subscriptions.update_one(
            {"subscription_id": subscription_id}, {"$set": {"status": "cancelled", "auto_renewal": False}}
        )
        return {"subscription_id": subscription_id, "status": "cancelled"}

    async def get_transaction_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """Complete transaction logs."""
        cursor = self.db.payments.find({"$or": [{"patient_id": user_id}, {"doctor_id": user_id}]}).sort("created_at", -1)
        return await cursor.to_list(length=None)
