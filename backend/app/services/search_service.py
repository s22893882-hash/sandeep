"""Search and recommendations business logic."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import re

from app.database import generate_id


class SearchService:
    """Service for managing searches and recommendations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database

    async def search_doctors(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Advanced doctor search."""
        search_filter = {}
        if query:
            # Simple regex search for demonstration.
            # In production, use Elasticsearch or MongoDB Text Search.
            regex = re.compile(query, re.IGNORECASE)
            search_filter["$or"] = [{"full_name": regex}, {"specialization": regex}, {"tags": {"$in": [regex]}}]

        if filters:
            if "specialization" in filters:
                search_filter["specialization"] = filters["specialization"]
            if "experience_years" in filters:
                search_filter["experience_years"] = {"$gte": filters["experience_years"]}
            if "rating" in filters:
                search_filter["rating"] = {"$gte": filters["rating"]}

        cursor = self.db.doctors.find(search_filter)
        return await cursor.to_list(length=None)

    async def find_nearby_doctors(self, lat: float, lng: float, radius_km: float = 10) -> List[Dict[str, Any]]:
        """Find doctors by location."""
        # Mock geospatial search
        cursor = self.db.doctors.find({})  # In reality, use $near
        return await cursor.to_list(length=10)

    async def search_by_specialization(self, specialization: str) -> List[Dict[str, Any]]:
        """Search by specialization."""
        cursor = self.db.doctors.find({"specialization": specialization})
        return await cursor.to_list(length=None)

    async def get_multi_filter_search(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Multi-filter search."""
        return await self.search_doctors("", filters)

    async def get_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized recommendations."""
        # Simple recommendation: doctors in user's most searched specialization
        history_cursor = self.db.search_history.find({"user_id": user_id}).sort("timestamp", -1).limit(5)
        history = await history_cursor.to_list(length=None)

        if not history:
            # Default recommendations
            cursor = self.db.doctors.find({}).sort("rating", -1).limit(5)
            return await cursor.to_list(length=None)

        # Mock recommendation logic
        cursor = self.db.doctors.find({}).limit(5)
        return await cursor.to_list(length=None)

    async def get_trending_doctors(self) -> List[Dict[str, Any]]:
        """Trending doctors/services."""
        cursor = self.db.doctors.find({}).sort("rating", -1).limit(5)
        return await cursor.to_list(length=None)

    async def save_search_criteria(self, user_id: str, name: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Save search criteria."""
        criteria_id = generate_id("SRC")
        doc = {
            "criteria_id": criteria_id,
            "user_id": user_id,
            "criteria_name": name,
            "filters": filters,
            "created_date": datetime.utcnow(),
        }
        await self.db.saved_search_criteria.insert_one(doc)
        return doc

    async def get_saved_criteria(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve saved searches."""
        cursor = self.db.saved_search_criteria.find({"user_id": user_id})
        return await cursor.to_list(length=None)

    async def autocomplete(self, query: str) -> List[str]:
        """Search autocomplete."""
        if not query:
            return []
        regex = re.compile(f"^{query}", re.IGNORECASE)
        # Combine results from specializations and doctor names
        names_cursor = self.db.doctors.find({"full_name": regex}, {"full_name": 1}).limit(5)
        specs_cursor = self.db.doctors.find({"specialization": regex}, {"specialization": 1}).limit(5)

        names = await names_cursor.to_list(length=None)
        specs = await specs_cursor.to_list(length=None)

        results = [n["full_name"] for n in names] + list(set([s["specialization"] for s in specs]))
        return results[:10]

    async def track_search(self, user_id: str, query: str, filters: Dict[str, Any]):
        """Track search history."""
        await self.db.search_history.insert_one(
            {"user_id": user_id, "query": query, "filters": filters, "timestamp": datetime.utcnow()}
        )
