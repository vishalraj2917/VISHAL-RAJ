from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PredictionHistoryItem(BaseModel):
    id: int
    timestamp: datetime
    predicted_aqi: float
    aqi_category: str
    color: str
    model_name: str
    location_id: int
    city: str
    latitude: float
    longitude: float
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    co: Optional[float] = None
    no2: Optional[float] = None
    so2: Optional[float] = None
    o3: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    pressure: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class PredictionHistoryResponse(BaseModel):
    success: bool = Field(True)
    count: int
    total: int
    history: List[PredictionHistoryItem]


class AnalyticsSummaryResponse(BaseModel):
    success: bool = Field(True)
    current_aqi: Optional[float] = None
    current_category: Optional[str] = None
    current_color: Optional[str] = None
    average_aqi: float
    min_aqi: float
    max_aqi: float
    total_predictions: int
    trend_direction: str  # "improving", "deteriorating", "stable"
    most_recent_timestamp: Optional[datetime] = None


class TrendPoint(BaseModel):
    timestamp: datetime
    aqi: float
    category: str
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None


class AnalyticsTrendsResponse(BaseModel):
    success: bool = Field(True)
    period_hours: int
    points_count: int
    trends: List[TrendPoint]
