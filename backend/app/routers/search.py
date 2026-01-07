"""Search and recommendations API endpoints."""
from fastapi import APIRouter, Depends
from typing import Optional, Dict, Any

from app.auth import get_current_user
from app.services.search_service import SearchService
from app.database import get_database

router = APIRouter(prefix="/api/search", tags=["search"])


def get_search_service(db=Depends(get_database)) -> SearchService:
    """Get search service instance."""
    return SearchService(db)


@router.post("/doctors", response_model=list)
async def search_doctors(
    query: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    current_user: Optional[dict] = Depends(get_current_user),
    service: SearchService = Depends(get_search_service),
):
    """Advanced doctor search."""
    if current_user:
        await service.track_search(current_user["user_id"], query or "", filters or {})
    return await service.search_doctors(query, filters)


@router.get("/doctors/nearby", response_model=list)
async def nearby_doctors(
    lat: float,
    lng: float,
    radius: float = 10.0,
    service: SearchService = Depends(get_search_service),
):
    """Find doctors by location."""
    return await service.find_nearby_doctors(lat, lng, radius)


@router.get("/doctors/specialization", response_model=list)
async def by_specialization(
    specialization: str,
    service: SearchService = Depends(get_search_service),
):
    """Search by specialization."""
    return await service.search_by_specialization(specialization)


@router.get("/doctors/filters", response_model=list)
async def by_filters(
    filters: Dict[str, Any] = Depends(),  # Simplify for now
    service: SearchService = Depends(get_search_service),
):
    """Multi-filter search."""
    return await service.get_multi_filter_search(filters)


@router.get("/recommendations", response_model=list)
async def recommendations(
    current_user: dict = Depends(get_current_user),
    service: SearchService = Depends(get_search_service),
):
    """Get personalized recommendations."""
    return await service.get_recommendations(current_user["user_id"])


@router.get("/trending", response_model=list)
async def trending(
    service: SearchService = Depends(get_search_service),
):
    """Trending doctors/services."""
    return await service.get_trending_doctors()


@router.post("/save-criteria", response_model=dict)
async def save_criteria(
    name: str,
    filters: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    service: SearchService = Depends(get_search_service),
):
    """Save search criteria."""
    return await service.save_search_criteria(current_user["user_id"], name, filters)


@router.get("/saved-criteria", response_model=list)
async def get_saved(
    current_user: dict = Depends(get_current_user),
    service: SearchService = Depends(get_search_service),
):
    """Retrieve saved searches."""
    return await service.get_saved_criteria(current_user["user_id"])


@router.post("/apply-filters", response_model=list)
async def apply_filters(
    filters: Dict[str, Any],
    service: SearchService = Depends(get_search_service),
):
    """Apply advanced filters."""
    return await service.get_multi_filter_search(filters)


@router.get("/autocomplete", response_model=list)
async def autocomplete(
    query: str,
    service: SearchService = Depends(get_search_service),
):
    """Search autocomplete."""
    return await service.autocomplete(query)
