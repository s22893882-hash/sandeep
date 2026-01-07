"""Analytics and reporting API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.auth import get_current_admin
from app.services.analytics_service import AnalyticsService
from app.database import get_database

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def get_analytics_service(db=Depends(get_database)) -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService(db)


@router.get("/platform-metrics", response_model=dict)
async def get_platform_metrics(
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Overall platform metrics."""
    return await service.get_platform_metrics()


@router.get("/doctor-performance", response_model=dict)
async def get_doctor_performance(
    doctor_id: str,
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Doctor performance metrics."""
    return await service.get_doctor_performance(doctor_id)


@router.get("/patient-engagement", response_model=dict)
async def get_patient_engagement(
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Patient engagement metrics."""
    return await service.get_patient_engagement()


@router.get("/revenue-dashboard", response_model=dict)
async def get_revenue_dashboard(
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Revenue & financial metrics."""
    return await service.get_revenue_dashboard()


@router.get("/appointment-trends", response_model=list)
async def get_appointment_trends(
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Appointment booking trends."""
    return await service.get_appointment_trends()


@router.get("/consultation-metrics", response_model=dict)
async def get_consultation_metrics(
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Consultation statistics."""
    return await service.get_consultation_metrics()


@router.get("/user-demographics", response_model=dict)
async def get_user_demographics(
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """User distribution & demographics."""
    return await service.get_user_demographics()


@router.get("/top-doctors", response_model=list)
async def get_top_doctors(
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Top performing doctors."""
    return await service.get_top_doctors()


@router.get("/health-insights", response_model=dict)
async def get_health_insights(
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Population health insights."""
    return await service.get_health_insights()


@router.get("/specialization-demand", response_model=dict)
async def get_specialization_demand(
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Demand by specialization."""
    return await service.get_specialization_demand()


@router.post("/reports/generate", response_model=dict)
async def generate_report(
    report_type: str,
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Generate custom report."""
    return await service.generate_report(report_type, current_user["user_id"])


@router.get("/reports/{id}", response_model=dict)
async def get_report(
    id: str,
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Retrieve generated report."""
    try:
        return await service.get_report(id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/real-time-dashboard", response_model=dict)
async def get_real_time_dashboard(
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Real-time metrics."""
    return await service.get_real_time_dashboard()


@router.post("/export", response_model=dict)
async def export_data(
    format: str = "csv",
    current_user: dict = Depends(get_current_admin),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Export analytics data."""
    return await service.export_analytics_data(format)
