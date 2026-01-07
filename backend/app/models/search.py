"""Search-related data models."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime


class SearchHistory(BaseModel):
    """Search history model."""

    user_id: str
    query: str
    filters: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SavedSearchCriteria(BaseModel):
    """Saved search criteria model."""

    criteria_id: str
    user_id: str
    criteria_name: str
    filters: Dict[str, Any]
    created_date: datetime = Field(default_factory=datetime.utcnow)


class DoctorSearchIndex(BaseModel):
    """Doctor search index model."""

    doctor_id: str
    full_name: str
    specialization: str
    experience_years: int
    rating: float
    location: Dict[str, Any]  # {lat, lng, address}
    tags: List[str]
    searchable_fields: List[str]
