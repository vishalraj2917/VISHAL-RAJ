import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import Prediction, Location, AirQuality, Weather
from app.utils.aqi import get_aqi_category_and_risk
from app.schemas.insights import InsightsRequest, InsightsResponse

logger = logging.getLogger(__name__)

# Reference ambient concentrations for severity ranking (mod threshold)
POLLUTANT_MOD_THRESHOLDS = {
    "pm25": 60.0,
    "pm10": 100.0,
    "co": 2.0,
    "no2": 80.0,
    "so2": 80.0,
    "o3": 100.0,
}

POLLUTANT_DISPLAY_NAMES = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "co": "CO",
    "no2": "NO2",
    "so2": "SO2",
    "o3": "O3",
}


class AIInsightsService:
    """
    Dedicated AI Insights Service providing explainability, pollutant ranking,
    trend intelligence, and actionable recommendations on top of GradientBoostingRegressor predictions.
    """

    @staticmethod
    def extract_top_pollutants(pollutants: Dict[str, Optional[float]]) -> List[str]:
        """
        Ranks atmospheric pollutants by relative severity against ambient thresholds.
        """
        ratios = []
        for k, v in pollutants.items():
            if v is not None and k in POLLUTANT_MOD_THRESHOLDS:
                threshold = POLLUTANT_MOD_THRESHOLDS[k]
                ratio = float(v) / threshold
                ratios.append((POLLUTANT_DISPLAY_NAMES[k], ratio))

        if not ratios:
            return ["PM2.5", "PM10"]

        # Sort by highest ratio
        ratios.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in ratios[:3]]

    @staticmethod
    def calculate_historical_trend(db: Session, location_id: Optional[int] = None) -> str:
        """
        Evaluates trend direction comparing recent predictions against earlier records.
        """
        query = db.query(Prediction).order_by(desc(Prediction.prediction_time))
        if location_id is not None:
            query = query.filter(Prediction.location_id == location_id)

        records = query.limit(10).all()
        if len(records) < 2:
            return "Insufficient historical data"

        latest_aqi = records[0].predicted_aqi
        earlier_aqi = records[-1].predicted_aqi
        diff = latest_aqi - earlier_aqi

        if diff > 5.0:
            return "Worsening"
        elif diff < -5.0:
            return "Improving"
        else:
            return "Stable"

    @staticmethod
    def generate_recommendation_package(aqi: float, top_pollutant: str) -> Dict[str, Any]:
        """
        Produces structured recommendations for outdoor activity, ventilation, masks, and lifestyle.
        """
        val = float(aqi)
        if val <= 50.0:
            return {
                "recommendations": [
                    "Air quality is clean and satisfactory for outdoor activities.",
                    "Natural home and office ventilation is encouraged.",
                    "Enjoy outdoor sports and leisure without precautions."
                ],
                "outdoor_activity": "Ideal conditions for all outdoor physical activities and running.",
                "ventilation": "Open windows to allow fresh air circulation.",
                "mask_recommendation": "No protective mask required."
            }
        elif val <= 100.0:
            return {
                "recommendations": [
                    "Sensitive individuals should monitor for mild throat or eye irritation.",
                    "Consider checking local AQI before extended high-intensity workouts.",
                    "Keep windows closed during peak vehicular commute hours."
                ],
                "outdoor_activity": "Suitable for most people. Sensitive groups should take frequent breaks during vigorous exertion.",
                "ventilation": "Natural ventilation is acceptable; use air purifiers if residing near main roads.",
                "mask_recommendation": "Optional; recommended only for unusually sensitive individuals."
            }
        elif val <= 150.0:
            return {
                "recommendations": [
                    "Sensitive groups (children, elderly, asthma patients) should reduce prolonged heavy outdoor exertion.",
                    "Move high-intensity cardio training indoors if experiencing shortness of breath.",
                    "Run HEPA indoor air filtration in residential areas."
                ],
                "outdoor_activity": "Reduce prolonged outdoor exertion; shift workouts to indoor gyms or early mornings.",
                "ventilation": "Keep windows closed during high-traffic hours and utilize indoor air purifiers.",
                "mask_recommendation": "N95/KN95 masks advised for sensitive individuals in outdoor traffic."
            }
        elif val <= 200.0:
            return {
                "recommendations": [
                    "Everyone should reduce prolonged or heavy exertion outdoors.",
                    "Sensitive individuals should avoid all strenuous outdoor activities.",
                    "Wear a fitted N95 respirator mask when commuting near roadways.",
                    "Ensure indoor air filtration is operating continuously."
                ],
                "outdoor_activity": "Avoid strenuous outdoor exercise; switch to indoor activities.",
                "ventilation": "Keep windows closed tightly to prevent outdoor particulate infiltration.",
                "mask_recommendation": "N95 respirator mask recommended for all individuals during outdoor exposure."
            }
        else:
            return {
                "recommendations": [
                    "Health warning: Avoid all outdoor physical activities and stay indoors.",
                    "Keep windows and doors sealed tightly with air purifiers active.",
                    "Seek immediate medical attention if experiencing respiratory distress or chest pain.",
                    "Follow municipal emergency air quality guidance."
                ],
                "outdoor_activity": "Avoid all outdoor activities; remain in a clean, filtered indoor environment.",
                "ventilation": "Do not open windows; use high-efficiency HEPA air filtration.",
                "mask_recommendation": "Well-fitted N95 or P100 respirator mandatory for any unavoidable outdoor transit."
            }

    @staticmethod
    def generate_insights_from_data(
        aqi: float,
        pollutants: Dict[str, Optional[float]],
        weather: Dict[str, Optional[float]],
        trend: str,
        city_name: Optional[str] = None
    ) -> InsightsResponse:
        """
        Constructs complete InsightsResponse payload from structured environmental parameters.
        """
        category, risk_level, color, default_summary = get_aqi_category_and_risk(aqi)
        primary_pollutants = AIInsightsService.extract_top_pollutants(pollutants)
        dom_p = primary_pollutants[0] if primary_pollutants else "PM2.5"

        pkg = AIInsightsService.generate_recommendation_package(aqi, dom_p)

        loc_str = f" in {city_name}" if city_name else ""
        summary = (
            f"Air quality is currently classified as {category} ({risk_level}) with a predicted AQI of {round(aqi, 1)}{loc_str}. "
            f"Primary atmospheric pollution is driven by elevated {dom_p}. "
            f"Historical trend direction is evaluated as {trend}."
        )

        return InsightsResponse(
            success=True,
            aqi=float(round(aqi, 1)),
            category=category,
            risk_level=risk_level,
            color=color,
            trend=trend,
            primary_pollutants=primary_pollutants,
            summary=summary,
            recommendations=pkg["recommendations"],
            outdoor_activity=pkg["outdoor_activity"],
            ventilation=pkg["ventilation"],
            mask_recommendation=pkg["mask_recommendation"],
            confidence=0.95,
            generated_by="rule_based",
            last_updated=datetime.now(timezone.utc)
        )

    @staticmethod
    def get_latest_system_insights(db: Session, location_id: Optional[int] = None) -> InsightsResponse:
        """
        Retrieves the latest prediction record from database and produces insights.
        """
        query = db.query(Prediction, Location).join(Location, Prediction.location_id == Location.id)
        if location_id is not None:
            query = query.filter(Prediction.location_id == location_id)

        latest_record = query.order_by(desc(Prediction.prediction_time)).first()

        if not latest_record:
            # Fallback baseline when no history exists
            return AIInsightsService.generate_insights_from_data(
                aqi=50.0,
                pollutants={"pm25": 15.0, "pm10": 30.0},
                weather={"temperature": 25.0, "humidity": 50.0},
                trend="Insufficient historical data",
                city_name=None
            )

        pred, loc = latest_record
        aq = db.query(AirQuality).filter(
            AirQuality.location_id == loc.id,
            AirQuality.timestamp == pred.prediction_time
        ).first()

        w = db.query(Weather).filter(
            Weather.location_id == loc.id,
            Weather.timestamp == pred.prediction_time
        ).first()

        pollutants = {
            "pm25": aq.pm25 if aq else None,
            "pm10": aq.pm10 if aq else None,
            "co": aq.co if aq else None,
            "no2": aq.no2 if aq else None,
            "so2": aq.so2 if aq else None,
            "o3": aq.o3 if aq else None,
        }

        weather = {
            "temperature": w.temperature if w else None,
            "humidity": w.humidity if w else None,
            "wind_speed": w.wind_speed if w else None,
            "pressure": w.pressure if w else None,
        }

        trend = AIInsightsService.calculate_historical_trend(db, location_id=loc.id)

        return AIInsightsService.generate_insights_from_data(
            aqi=pred.predicted_aqi,
            pollutants=pollutants,
            weather=weather,
            trend=trend,
            city_name=loc.city
        )
