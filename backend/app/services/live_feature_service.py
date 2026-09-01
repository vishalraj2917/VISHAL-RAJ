import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
import zoneinfo
import numpy as np

from app.schemas.prediction import PredictionRequest

logger = logging.getLogger(__name__)


class LiveFeatureService:
    """
    Transforms live external API weather and air quality dictionaries into
    the exact 21 ML features expected by the trained model pipeline.
    Reuses Phase 4/5 mathematical formulations with strict numerical consistency.
    """

    @staticmethod
    def parse_observation_time(
        timestamp_str: Optional[str] = None,
        tz_name: Optional[str] = "UTC",
    ) -> datetime:
        """
        Parses observation timestamp respecting provider's local timezone.
        """
        if not timestamp_str:
            return datetime.now(timezone.utc)

        try:
            # Parse ISO format (e.g. 2026-09-01T14:00)
            dt = datetime.fromisoformat(timestamp_str)
            if dt.tzinfo is None:
                try:
                    tz = zoneinfo.ZoneInfo(tz_name or "UTC")
                    dt = dt.replace(tzinfo=tz)
                except Exception:
                    dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return datetime.now(timezone.utc)

    @classmethod
    def build_features(
        cls,
        air_quality: Dict[str, Any],
        weather: Dict[str, Any],
        location_id: Optional[int] = None,
    ) -> Tuple[PredictionRequest, Dict[str, Any]]:
        """
        Extracts pollutants, weather, temporal parameters, and domain interactions.
        Returns validated PredictionRequest instance and raw feature dictionary.
        """
        # 1. Primary Pollutants
        pm25 = float(air_quality["pm25"])
        pm10 = float(air_quality["pm10"])
        co = float(air_quality["co"])
        no2 = float(air_quality["no2"])
        so2 = float(air_quality["so2"])
        o3 = float(air_quality["o3"])

        # 2. Meteorological Variables
        temperature = float(weather["temperature"])
        humidity = float(weather["humidity"])
        wind_speed = float(weather["wind_speed"])
        pressure = float(weather["pressure"])

        # 3. Time & Temporal Features
        obs_time_str = weather.get("timestamp") or air_quality.get("timestamp")
        tz_name = weather.get("timezone") or air_quality.get("timezone") or "UTC"
        obs_dt = cls.parse_observation_time(obs_time_str, tz_name)

        hour = int(obs_dt.hour)
        day = int(obs_dt.day)
        month = int(obs_dt.month)
        day_of_week = int(obs_dt.weekday())  # 0 for Monday to 6 for Sunday
        is_weekend = int(1 if day_of_week in (5, 6) else 0)

        # 4. Cyclical Encodings (Exact Phase 4 formulas)
        hour_sin = float(np.sin(2 * np.pi * hour / 24.0))
        hour_cos = float(np.cos(2 * np.pi * hour / 24.0))
        month_sin = float(np.sin(2 * np.pi * (month - 1) / 12.0))
        month_cos = float(np.cos(2 * np.pi * (month - 1) / 12.0))

        # 5. Domain Interaction Features (Exact Phase 4 formulas)
        # pm_ratio = (pm25 / (pm10 + 1e-5)).clip(0.0, 1.5)
        pm_ratio = float(np.clip(pm25 / (pm10 + 1e-5), 0.0, 1.5))

        # temp_humidity_idx = (temperature * humidity) / 100.0
        temp_humidity_idx = float((temperature * humidity) / 100.0)

        raw_features = {
            "pm25": pm25,
            "pm10": pm10,
            "co": co,
            "no2": no2,
            "so2": so2,
            "o3": o3,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "pressure": pressure,
            "hour": hour,
            "day": day,
            "month": month,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "hour_sin": hour_sin,
            "hour_cos": hour_cos,
            "month_sin": month_sin,
            "month_cos": month_cos,
            "pm_ratio": pm_ratio,
            "temp_humidity_idx": temp_humidity_idx,
            "location_id": location_id,
        }

        # Build and validate using Pydantic schema
        prediction_request = PredictionRequest(**raw_features)
        return prediction_request, raw_features
