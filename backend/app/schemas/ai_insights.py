from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DominantPollutantAnalysis(BaseModel):
    dominant_pollutant: str
    secondary_pollutant: Optional[str] = None
    pollutant_values: Dict[str, Optional[float]]
    explanation: str


class TrendIntelligence(BaseModel):
    direction: str  # "improving", "stable", "worsening", "insufficient_data"
    percentage_change: Optional[float] = None
    explanation: str


class SmartAlert(BaseModel):
    severity: str  # "info", "warning", "danger"
    title: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SmartAlertsResponse(BaseModel):
    success: bool = Field(True)
    count: int
    alerts: List[SmartAlert]


class AIInsightsResponse(BaseModel):
    success: bool = Field(True)
    current_aqi: Optional[float] = None
    aqi_category: str
    risk_level: str
    summary: str
    dominant_pollutants: DominantPollutantAnalysis
    health_advice: List[str]
    environmental_factors: List[str]
    trend: TrendIntelligence
    recommendations: List[str]
    model_provenance: str = "GradientBoostingRegressor"
    disclaimer: str = "This information is for general environmental awareness and does not replace professional medical advice."
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
