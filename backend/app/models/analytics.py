"""Analytics-related data models."""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class Metric(BaseModel):
    """Metric model."""

    metric_name: str
    value: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dimensions: Dict[str, str] = {}


class ReportRequest(BaseModel):
    """Report generation request model."""

    report_type: str
    start_date: datetime
    end_date: datetime
    parameters: Dict[str, Any] = {}


class ReportResponse(BaseModel):
    """Report response model."""

    report_id: str
    report_type: str
    generated_by: str
    generation_date: datetime
    data: Any
    download_url: Optional[str] = None


class MetricsCache(BaseModel):
    """Metrics cache model."""

    metric_key: str
    value: Any
    last_updated: datetime
