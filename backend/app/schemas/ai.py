from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class EnvironmentalContext(BaseModel):
    """
    Structured environmental context provided to AI features.
    """
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    city_name: Optional[str] = None
    predicted_aqi: Optional[float] = Field(None, ge=0.0, le=1000.0)
    aqi_category: Optional[str] = None
    dominant_pollutant: Optional[str] = None
    pm25: Optional[float] = Field(None, ge=0.0)
    pm10: Optional[float] = Field(None, ge=0.0)
    co: Optional[float] = Field(None, ge=0.0)
    no2: Optional[float] = Field(None, ge=0.0)
    so2: Optional[float] = Field(None, ge=0.0)
    o3: Optional[float] = Field(None, ge=0.0)
    temperature: Optional[float] = None
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0)
    wind_speed: Optional[float] = Field(None, ge=0.0)
    pressure: Optional[float] = None
    observed_at: Optional[str] = None


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of message author: 'user' or 'assistant'")
    content: str = Field(..., max_length=2000, description="Text message content")


class AIChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question regarding air quality, pollutants, or safety"
    )
    context: Optional[EnvironmentalContext] = Field(
        default=None,
        description="Current environmental telemetry & ML AQI prediction context"
    )
    history: Optional[List[ChatMessage]] = Field(
        default=[],
        max_length=20,
        description="Recent conversation history for multi-turn context"
    )

    @field_validator("message")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("User message cannot be empty or whitespace only.")
        return trimmed

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Is it safe to go for a run right now?",
                "context": {
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "predicted_aqi": 68.5,
                    "aqi_category": "Moderate",
                    "dominant_pollutant": "PM2.5",
                    "pm25": 28.4,
                    "pm10": 55.2,
                    "temperature": 27.5,
                    "humidity": 60.0
                }
            }
        }
    )


class AIChatResponse(BaseModel):
    success: bool = Field(True)
    reply: str = Field(..., description="AI-generated explanatory reply")
    context_used: bool = Field(..., description="Indicates if environmental context was provided")
    disclaimer: str = Field(
        "This information is for general awareness and does not replace medical advice from a qualified healthcare professional.",
        description="Medical safety boundary disclaimer"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AIReportRequest(BaseModel):
    context: EnvironmentalContext = Field(
        ...,
        description="Current environmental and predicted AQI context for generating the report"
    )


class AIReportSections(BaseModel):
    summary: str = Field(..., description="Overall executive summary of current air quality")
    air_quality_analysis: str = Field(..., description="Detailed breakdown of AQI and pollutant factors")
    weather_impact: str = Field(..., description="Analysis of how temperature, wind, and humidity affect pollution dispersal")
    safety_recommendations: List[str] = Field(..., description="Actionable safety guidance for public and sensitive groups")


class AIReportResponse(BaseModel):
    success: bool = Field(True)
    report: AIReportSections = Field(..., description="Structured air quality report")
    disclaimer: str = Field(
        "This report is generated using AI analysis of current environmental readings and does not constitute medical advice.",
        description="Standard advisory disclaimer"
    )
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AIHealthAdviceRequest(BaseModel):
    activity: str = Field(
        "General Outdoor Activity",
        max_length=100,
        description="Planned activity (e.g. Outdoor Exercise, Commuting, Cycling, Outdoor Work)"
    )
    target_group: Optional[str] = Field(
        "General Public",
        max_length=100,
        description="Audience group (e.g. General Public, Sensitive / Children / Elderly, Athletes)"
    )
    context: EnvironmentalContext = Field(
        ...,
        description="Current telemetry and ML predicted AQI data"
    )


class AIHealthAdviceResponse(BaseModel):
    success: bool = Field(True)
    activity: str = Field(...)
    target_group: str = Field(...)
    aqi_level: Optional[float] = Field(None)
    safety_rating: str = Field(..., description="Safe, Caution, or Unfavorable")
    advice: str = Field(..., description="Personalized environmental health advice")
    recommended_precautions: List[str] = Field(..., description="Specific preventive actions (e.g. masks, timing, hydration)")
    disclaimer: str = Field(
        "This information is for general awareness and does not replace advice from a qualified healthcare professional.",
        description="Medical safety disclaimer"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
