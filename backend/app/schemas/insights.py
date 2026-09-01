from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class InsightsRequest(BaseModel):
    """
    Request payload to generate on-demand insights for specific atmospheric measurements.
    """
    aqi: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Predicted AQI value (computed automatically if omitted)")
    pm25: Optional[float] = Field(None, ge=0.0, le=1000.0, description="PM2.5 concentration in µg/m³")
    pm10: Optional[float] = Field(None, ge=0.0, le=1500.0, description="PM10 concentration in µg/m³")
    co: Optional[float] = Field(None, ge=0.0, le=100.0, description="CO concentration in mg/m³")
    no2: Optional[float] = Field(None, ge=0.0, le=1000.0, description="NO2 concentration in µg/m³")
    so2: Optional[float] = Field(None, ge=0.0, le=1000.0, description="SO2 concentration in µg/m³")
    o3: Optional[float] = Field(None, ge=0.0, le=1000.0, description="O3 concentration in µg/m³")
    temperature: Optional[float] = Field(None, ge=-50.0, le=60.0, description="Temperature in °C")
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity in %")
    wind_speed: Optional[float] = Field(None, ge=0.0, le=150.0, description="Wind speed in km/h")
    pressure: Optional[float] = Field(None, ge=800.0, le=1100.0, description="Pressure in hPa")
    location_id: Optional[int] = Field(None, description="Optional registered location ID")


class InsightsResponse(BaseModel):
    """
    Structured AI insights response payload.
    """
    success: bool = Field(True)
    aqi: float = Field(..., description="Continuous Air Quality Index")
    category: str = Field(..., description="Standard qualitative category")
    risk_level: str = Field(..., description="Risk assessment level")
    color: str = Field(..., description="Hex color token")
    trend: str = Field(..., description="Trajectory: Improving, Stable, Worsening, or Insufficient historical data")
    primary_pollutants: List[str] = Field(..., description="Top contributing pollutants in descending order of severity")
    summary: str = Field(..., description="Human-readable synthesis of current air quality and impact")
    recommendations: List[str] = Field(..., description="Actionable health and exposure reduction recommendations")
    outdoor_activity: str = Field(..., description="Guidance for outdoor exercise and activities")
    ventilation: str = Field(..., description="Indoor ventilation & air purifier advice")
    mask_recommendation: str = Field(..., description="N95/particulate respirator recommendation")
    confidence: float = Field(0.95, description="Inference confidence score")
    generated_by: str = Field("rule_based", description="Insight generation engine: 'rule_based' or 'llm_augmented'")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "aqi": 82.5,
                "category": "Moderate",
                "risk_level": "Moderate Risk",
                "color": "#F59E0B",
                "trend": "Stable",
                "primary_pollutants": ["PM2.5", "PM10"],
                "summary": "Air quality is acceptable for the general public, but sensitive individuals may experience minor irritation.",
                "recommendations": [
                    "Sensitive individuals should reduce prolonged outdoor activity.",
                    "Consider keeping windows closed during morning traffic peaks.",
                    "Monitor AQI before exercising outdoors."
                ],
                "outdoor_activity": "Acceptable for general outdoor activities. Sensitive groups should take frequent breaks.",
                "ventilation": "Natural ventilation is acceptable; use indoor air filtration if living near busy arterial roads.",
                "mask_recommendation": "Not strictly required for the general public; recommended for unusually sensitive individuals during prolonged exposure.",
                "confidence": 0.95,
                "generated_by": "rule_based",
                "last_updated": "2026-09-01T14:55:00Z"
            }
        }
    )
