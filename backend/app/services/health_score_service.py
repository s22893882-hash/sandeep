"""Health score calculation service."""
from typing import Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.patient import HealthScoreResponse, HealthScoreComponents


class HealthScoreService:
    """Service for calculating patient health scores."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    def _calculate_bmi(self, height_cm: float, weight_kg: float) -> float:
        """Calculate BMI from height and weight."""
        height_m = height_cm / 100
        if height_m <= 0:
            return 0
        return round(weight_kg / (height_m**2), 2)

    def _calculate_bmi_component(self, bmi: float) -> float:
        """Calculate BMI component score (30% weight)."""
        optimal_bmi = 22.5
        component = 100 - (abs(bmi - optimal_bmi) * 2)
        return max(0, min(100, round(component, 2)))

    def _estimate_medication_count(self, patient_id: str) -> int:
        """Estimate medication count from medical history notes."""
        # This is a simplified estimation - in production, you'd have a separate medications table
        # We'll use the count of active conditions as a proxy for medication count
        return 0  # Will be calculated in async method

    def _calculate_medications_component(self, medication_count: int) -> float:
        """Calculate medications component score (20% weight)."""
        component = 100 - (medication_count * 10)
        return max(0, min(100, round(component, 2)))

    def _calculate_conditions_component(self, active_conditions_count: int) -> float:
        """Calculate conditions component score (40% weight)."""
        component = 100 - (active_conditions_count * 15)
        return max(0, min(100, round(component, 2)))

    def _calculate_appointments_component(self, recent_appointments: int) -> float:
        """Calculate appointments component score (10% weight)."""
        # Normalize: 4 or more appointments = full score
        normalized = min(recent_appointments / 4, 1)
        return round(normalized * 100, 2)

    async def _get_active_conditions_count(self, patient_id: str) -> int:
        """Get count of active medical conditions."""
        count = await self.db.medical_history.count_documents({"patient_id": patient_id, "status": "active"})
        return count

    async def _get_medications_count(self, patient_id: str) -> int:
        """Get count of medications from treatment notes."""
        # Parse treatment notes for medication mentions
        history_records = await self.db.medical_history.find(
            {"patient_id": patient_id, "status": "active"},
            {"treatment_notes": 1},
        ).to_list(length=None)

        medication_keywords = [
            "medication",
            "medicine",
            "pill",
            "tablet",
            "drug",
            "dosage",
            "prescription",
            "mg",
            "mg/ml",
        ]

        medication_count = 0
        for record in history_records:
            notes = record.get("treatment_notes", "")
            if notes:
                # Count medication keyword mentions as a rough estimate
                for keyword in medication_keywords:
                    medication_count += notes.lower().count(keyword)

        # Cap at a reasonable maximum
        return min(medication_count // 2, 10)  # Divide by 2 to avoid overcounting

    async def _get_recent_appointments_count(self, patient_id: str) -> int:
        """Get count of appointments in last 3 months."""
        three_months_ago = datetime.utcnow() - timedelta(days=90)

        # In production, you'd query the appointments collection
        # For now, we'll simulate with medical history entries
        count = await self.db.medical_history.count_documents(
            {
                "patient_id": patient_id,
                "created_at": {"$gte": three_months_ago},
            }
        )

        # Use a reasonable estimation for demo purposes
        return min(count, 5)

    async def calculate_health_score(self, patient_id: str, patient_data: Dict[str, Any]) -> HealthScoreResponse:
        """Calculate overall health score for a patient."""
        # Get BMI
        bmi = self._calculate_bmi(patient_data.get("height_cm", 170), patient_data.get("weight_kg", 70))

        # Get component scores
        bmi_component = self._calculate_bmi_component(bmi)
        active_conditions_count = await self._get_active_conditions_count(patient_id)
        conditions_component = self._calculate_conditions_component(active_conditions_count)
        medication_count = await self._get_medications_count(patient_id)
        medications_component = self._calculate_medications_component(medication_count)
        recent_appointments = await self._get_recent_appointments_count(patient_id)
        appointments_component = self._calculate_appointments_component(recent_appointments)

        # Calculate weighted overall score
        health_score = (
            (bmi_component * 0.30)
            + (conditions_component * 0.40)
            + (medications_component * 0.20)
            + (appointments_component * 0.10)
        )

        # Build response
        components = HealthScoreComponents(
            bmi=bmi,
            bmi_component=bmi_component,
            active_conditions_count=active_conditions_count,
            conditions_component=conditions_component,
            medication_count=medication_count,
            medications_component=medications_component,
            recent_appointments=recent_appointments,
            appointments_component=appointments_component,
        )

        return HealthScoreResponse(
            health_score=int(round(health_score)),
            score_components=components,
            last_updated=datetime.utcnow(),
        )
