"""Analytics and reporting business logic."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import generate_id


class AnalyticsService:
    """Service for managing analytics."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def get_platform_metrics(self) -> Dict[str, Any]:
        """Overall platform metrics."""
        user_count = await self.db.users.count_documents({})
        appointment_count = await self.db.appointments.count_documents({})
        consultation_count = await self.db.consultations.count_documents({})

        return {
            "total_users": user_count,
            "total_appointments": appointment_count,
            "total_consultations": consultation_count,
            "timestamp": datetime.utcnow(),
        }

    async def get_doctor_performance(self, doctor_id: str) -> Dict[str, Any]:
        """Doctor performance metrics."""
        completed = await self.db.appointments.count_documents({"doctor_id": doctor_id, "status": "completed"})
        total = await self.db.appointments.count_documents({"doctor_id": doctor_id})

        rating_cursor = self.db.consultation_feedback.find({"doctor_id": doctor_id})
        ratings = await rating_cursor.to_list(length=None)
        avg_rating = sum(r["rating"] for r in ratings) / len(ratings) if ratings else 0

        return {
            "doctor_id": doctor_id,
            "completion_rate": (completed / total) if total else 0,
            "average_rating": avg_rating,
            "total_consultations": len(ratings),
        }

    async def get_patient_engagement(self) -> Dict[str, Any]:
        """Patient engagement metrics."""
        # Mock metrics
        return {"active_daily_users": 150, "average_session_duration": 12, "retention_rate": 0.85}  # minutes

    async def get_revenue_dashboard(self) -> Dict[str, Any]:
        """Revenue & financial metrics."""
        cursor = self.db.payments.find({"status": "completed"})
        payments = await cursor.to_list(length=None)
        total_revenue = sum(p["amount"] for p in payments)

        return {"total_revenue": total_revenue, "currency": "USD", "transaction_count": len(payments), "period": "all_time"}

    async def get_appointment_trends(self) -> List[Dict[str, Any]]:
        """Appointment booking trends."""
        # Simple daily count for last 7 days
        trends = []
        for i in range(7):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            count = await self.db.appointments.count_documents({"appointment_date": date})
            trends.append({"date": date, "count": count})
        return trends

    async def get_consultation_metrics(self) -> Dict[str, Any]:
        """Consultation statistics."""
        cursor = self.db.consultations.find({"status": "completed"})
        consultations = await cursor.to_list(length=None)
        avg_duration = sum(c.get("duration", 0) for c in consultations) / len(consultations) if consultations else 0

        return {"average_consultation_duration": avg_duration, "total_completed": len(consultations)}

    async def get_user_demographics(self) -> Dict[str, Any]:
        """User distribution & demographics."""
        # Mock demographics
        return {
            "gender_distribution": {"male": 0.48, "female": 0.52},
            "age_groups": {"18-25": 0.2, "26-40": 0.5, "41-60": 0.2, "60+": 0.1},
        }

    async def get_top_doctors(self) -> List[Dict[str, Any]]:
        """Top performing doctors."""
        # Mock top doctors
        return [
            {"doctor_id": "doc1", "name": "Dr. Smith", "score": 98},
            {"doctor_id": "doc2", "name": "Dr. Jones", "score": 95},
        ]

    async def get_health_insights(self) -> Dict[str, Any]:
        """Population health insights."""
        return {"common_conditions": ["hypertension", "diabetes", "asthma"], "average_health_score": 75}

    async def get_specialization_demand(self) -> Dict[str, Any]:
        """Demand by specialization."""
        return {"cardiology": 120, "dermatology": 85, "pediatrics": 95}

    async def generate_report(self, report_type: str, generated_by: str) -> Dict[str, Any]:
        """Generate custom report."""
        report_id = generate_id("REP")
        report_doc = {
            "report_id": report_id,
            "report_type": report_type,
            "generated_by": generated_by,
            "generation_date": datetime.utcnow(),
            "data": {"summary": "This is a mock report data"},
            "status": "completed",
        }
        await self.db.reports.insert_one(report_doc)
        return report_doc

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieve generated report."""
        report = await self.db.reports.find_one({"report_id": report_id})
        if not report:
            raise ValueError("Report not found")
        return report

    async def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Real-time metrics."""
        return {"online_users": 25, "active_consultations": 5, "pending_appointments": 12}

    async def export_analytics_data(self, format: str = "csv") -> Dict[str, Any]:
        """Export analytics data."""
        return {"export_url": f"https://api.federatedhealth.ai/export/analytics.{format}"}
