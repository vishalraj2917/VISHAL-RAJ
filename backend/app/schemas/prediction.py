from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
import math


class LocationCoordinates(BaseModel):
    """
    Geographic coordinates input for live queries.
    """
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (-90.0 to 90.0)"
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (-180.0 to 180.0)"
    )
    city_name: Optional[str] = Field(
        default=None,
        description="Optional human-readable city or location name"
    )

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def validate_finite_coords(cls, v: Any, info) -> float:
        if v is None:
            raise ValueError(f"Coordinate '{info.field_name}' cannot be None")
        try:
            val = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"Coordinate '{info.field_name}' must be a valid float")
        if math.isnan(val) or math.isinf(val):
            raise ValueError(f"Coordinate '{info.field_name}' must be a finite numerical value")
        return val

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "city_name": "Bengaluru"
            }
        }
    )


class LivePollutantData(BaseModel):
    pm25: float = Field(..., description="PM2.5 concentration (µg/m³)")
    pm10: float = Field(..., description="PM10 concentration (µg/m³)")
    co: float = Field(..., description="Carbon Monoxide concentration (mg/m³)")
    no2: float = Field(..., description="Nitrogen Dioxide concentration (µg/m³)")
    so2: float = Field(..., description="Sulfur Dioxide concentration (µg/m³)")
    o3: float = Field(..., description="Ozone concentration (µg/m³)")


class LiveWeatherData(BaseModel):
    temperature: float = Field(..., description="Ambient temperature in °C")
    humidity: float = Field(..., description="Relative humidity in %")
    wind_speed: float = Field(..., description="Wind speed in km/h")
    pressure: float = Field(..., description="Surface pressure in hPa")


class LivePredictionRequest(BaseModel):
    """
    Request payload for live environmental forecasting by latitude & longitude.
    """
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude of target location (-90.0 to 90.0)"
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude of target location (-180.0 to 180.0)"
    )
    location_id: Optional[int] = Field(
        default=None,
        description="Optional registered database Location ID to attach history"
    )

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def validate_finite_coords(cls, v: Any, info) -> float:
        if v is None:
            raise ValueError(f"Coordinate '{info.field_name}' cannot be None")
        try:
            val = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"Coordinate '{info.field_name}' must be a valid float")
        if math.isnan(val) or math.isinf(val):
            raise ValueError(f"Coordinate '{info.field_name}' must be a finite numerical value")
        return val

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": 12.9716,
                "longitude": 77.5946
            }
        }
    )


class PredictionRequest(BaseModel):
    """
    Pydantic schema for individual AQI prediction requests.
    Enforces strict physical boundaries and data types for all input features.
    """
    # Core Pollutants
    pm25: float = Field(
        ...,
        ge=0.0,
        le=1000.0,
        description="Particulate Matter PM2.5 concentration in µg/m³ (0 to 1000)"
    )
    pm10: float = Field(
        ...,
        ge=0.0,
        le=1500.0,
        description="Particulate Matter PM10 concentration in µg/m³ (0 to 1500)"
    )
    co: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Carbon Monoxide concentration in mg/m³ (0 to 100)"
    )
    no2: float = Field(
        ...,
        ge=0.0,
        le=1000.0,
        description="Nitrogen Dioxide concentration in µg/m³ (0 to 1000)"
    )
    so2: float = Field(
        ...,
        ge=0.0,
        le=1000.0,
        description="Sulfur Dioxide concentration in µg/m³ (0 to 1000)"
    )
    o3: float = Field(
        ...,
        ge=0.0,
        le=1000.0,
        description="Ozone concentration in µg/m³ (0 to 1000)"
    )

    # Weather Parameters
    temperature: float = Field(
        ...,
        ge=-50.0,
        le=60.0,
        description="Ambient temperature in °C (-50 to 60)"
    )
    humidity: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Relative humidity in % (0 to 100)"
    )
    wind_speed: float = Field(
        ...,
        ge=0.0,
        le=150.0,
        description="Wind speed in km/h or m/s normalized (0 to 150)"
    )
    pressure: float = Field(
        ...,
        ge=800.0,
        le=1100.0,
        description="Atmospheric pressure in hPa (800 to 1100)"
    )

    # Temporal Parameters
    hour: int = Field(
        ...,
        ge=0,
        le=23,
        description="Hour of day in 24-hour format (0 to 23)"
    )
    day: int = Field(
        ...,
        ge=1,
        le=31,
        description="Day of the month (1 to 31)"
    )
    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Month of the year (1 to 12)"
    )
    day_of_week: int = Field(
        ...,
        ge=0,
        le=6,
        description="Day of the week: 0 for Monday to 6 for Sunday"
    )
    is_weekend: int = Field(
        ...,
        ge=0,
        le=1,
        description="Weekend flag: 1 if Saturday/Sunday, 0 otherwise"
    )

    # Optional Derived / Advanced Features (automatically calculated by backend if omitted)
    hour_sin: Optional[float] = Field(
        default=None,
        description="Cyclical sine transformation for hour"
    )
    hour_cos: Optional[float] = Field(
        default=None,
        description="Cyclical cosine transformation for hour"
    )
    month_sin: Optional[float] = Field(
        default=None,
        description="Cyclical sine transformation for month"
    )
    month_cos: Optional[float] = Field(
        default=None,
        description="Cyclical cosine transformation for month"
    )
    pm_ratio: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.5,
        description="Ratio of PM2.5 to PM10"
    )
    temp_humidity_idx: Optional[float] = Field(
        default=None,
        description="Temperature and humidity interaction index"
    )

    # Contextual metadata (optional)
    location_id: Optional[int] = Field(
        default=None,
        description="Optional location ID if associating with registered station"
    )

    @field_validator(
        "pm25", "pm10", "co", "no2", "so2", "o3",
        "temperature", "humidity", "wind_speed", "pressure",
        mode="before"
    )
    @classmethod
    def validate_finite_floats(cls, v: Any, info) -> float:
        if v is None:
            raise ValueError(f"Field '{info.field_name}' cannot be None")
        try:
            val = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"Field '{info.field_name}' must be a valid float")
        if math.isnan(val) or math.isinf(val):
            raise ValueError(f"Field '{info.field_name}' must be a finite numerical value")
        return val

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pm25": 45.2,
                "pm10": 85.0,
                "co": 0.8,
                "no2": 24.5,
                "so2": 11.2,
                "o3": 28.0,
                "temperature": 27.5,
                "humidity": 62.0,
                "wind_speed": 3.8,
                "pressure": 1012.5,
                "hour": 14,
                "day": 15,
                "month": 6,
                "day_of_week": 2,
                "is_weekend": 0
            }
        }
    )


class ModelInfo(BaseModel):
    name: str = Field(..., description="Name of the trained machine learning model")
    type: str = Field(..., description="Model architecture type")
    target: str = Field("aqi", description="Target variable name")
    validation_rmse: Optional[float] = Field(None, description="Validation RMSE score")
    test_rmse: Optional[float] = Field(None, description="Final test RMSE score")


class PredictionData(BaseModel):
    aqi: float = Field(..., description="Predicted continuous Air Quality Index (AQI)")
    category: str = Field(..., description="AQI qualitative category (e.g., Good, Moderate, Unhealthy)")
    color: str = Field(..., description="Hex color code associated with AQI category")
    dominant_pollutant: Optional[str] = Field(None, description="Primary contributing pollutant")
    health_advisory: Optional[str] = Field(None, description="General health advice for this AQI level")


class PredictionResponse(BaseModel):
    """
    Standardized API response for AQI predictions.
    """
    success: bool = Field(True, description="Indicates if prediction was successfully computed")
    prediction: PredictionData = Field(..., description="Prediction details and categories")
    model: ModelInfo = Field(..., description="Model provenance and version information")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the prediction execution"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "prediction": {
                    "aqi": 68.87,
                    "category": "Moderate",
                    "color": "#FBBF24",
                    "dominant_pollutant": "PM2.5",
                    "health_advisory": "Air quality is acceptable; sensitive individuals should take precautions."
                },
                "model": {
                    "name": "Gradient Boosting",
                    "type": "GradientBoostingRegressor",
                    "target": "aqi",
                    "validation_rmse": 1.1772,
                    "test_rmse": 1.3798
                },
                "timestamp": "2026-09-01T14:15:00.000000Z"
            }
        }
    )


class LivePredictionResponse(BaseModel):
    """
    Comprehensive response containing live normalized inputs, weather, and ML prediction.
    """
    success: bool = Field(True, description="Success indicator")
    location: LocationCoordinates = Field(..., description="Queried geographic coordinates")
    air_quality: LivePollutantData = Field(..., description="Normalized live pollutant concentrations")
    weather: LiveWeatherData = Field(..., description="Normalized live meteorological conditions")
    prediction: PredictionData = Field(..., description="Computed AQI prediction and health advisory")
    model: ModelInfo = Field(..., description="Active ML model provenance")
    observed_at: str = Field(..., description="Timestamp of live environmental observation")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response execution timestamp in UTC"
    )


class BatchPredictionRequest(BaseModel):
    records: List[PredictionRequest] = Field(..., min_length=1, max_length=100, description="List of prediction inputs")


class BatchPredictionResponse(BaseModel):
    success: bool = Field(True)
    count: int = Field(...)
    predictions: List[PredictionData] = Field(...)
    model: ModelInfo = Field(...)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
