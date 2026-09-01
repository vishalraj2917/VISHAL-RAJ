import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import Prediction, Location, AirQuality, Weather
from app.services.prediction_service import get_aqi_category_info
from app.schemas.ai_insights import (
    DominantPollutantAnalysis,
    TrendIntelligence,
    SmartAlert,
    SmartAlertsResponse,
    AIInsightsResponse,
)

logger = logging.getLogger(__name__)

# Standard ambient reference thresholds (µg/m³, mg/m³ for CO) for relative severity normalization
POLLUTANT_THRESHOLDS = {
    "pm25": {"unit": "µg/m³", "good": 30.0, "mod": 60.0, "severe": 120.0, "name": "Fine Particulate Matter (PM2.5)"},
    "pm10": {"unit": "µg/m³", "good": 50.0, "mod": 100.0, "severe": 250.0, "name": "Coarse Particulate Matter (PM10)"},
    "co": {"unit": "mg/m³", "good": 1.0, "mod": 2.0, "severe": 10.0, "name": "Carbon Monoxide (CO)"},
    "no2": {"unit": "µg/m³", "good": 40.0, "mod": 80.0, "severe": 180.0, "name": "Nitrogen Dioxide (NO2)"},
    "so2": {"unit": "µg/m³", "good": 40.0, "mod": 80.0, "severe": 380.0, "name": "Sulfur Dioxide (SO2)"},
    "o3": {"unit": "µg/m³", "good": 50.0, "mod": 100.0, "severe": 168.0, "name": "Ground-level Ozone (O3)"},
}


class AIInsightEngine:
    """
    Intelligent AI insight generation, dominant pollutant detection,
    trend intelligence, and smart alerts engine.
    Complements the GradientBoostingRegressor numerical predictions.
    """

    @staticmethod
    def analyze_dominant_pollutants(pollutants: Dict[str, Optional[float]]) -> DominantPollutantAnalysis:
        """
        Evaluates normalized severity ratio across all available pollutants to identify dominant & secondary contributors.
        """
        ratios = {}
        for k, v in pollutants.items():
            if v is not None and k in POLLUTANT_THRESHOLDS:
                ref = POLLUTANT_THRESHOLDS[k]["mod"]
                ratios[k] = v / ref if ref > 0 else 0.0

        if not ratios:
            return DominantPollutantAnalysis(
                dominant_pollutant="PM2.5",
                secondary_pollutant=None,
                pollutant_values=pollutants,
                explanation="No pollutant measurements available for contribution analysis."
            )

        sorted_pollutants = sorted(ratios.items(), key=lambda item: item[1], reverse=True)
        dominant_key = sorted_pollutants[0][0]
        secondary_key = sorted_pollutants[1][0] if len(sorted_pollutants) > 1 else None

        dom_info = POLLUTANT_THRESHOLDS[dominant_key]
        dom_val = pollutants.get(dominant_key)
        dom_name = dom_info["name"]

        explanation = f"{dom_name} is currently the dominant atmospheric pollutant ({dom_val} {dom_info['unit']}), contributing most significantly to the evaluated air quality index."
        if secondary_key:
            sec_info = POLLUTANT_THRESHOLDS[secondary_key]
            sec_val = pollutants.get(secondary_key)
            explanation += f" Secondary contributor is {sec_info['name']} at {sec_val} {sec_info['unit']}."

        return DominantPollutantAnalysis(
            dominant_pollutant=dominant_key.upper(),
            secondary_pollutant=secondary_key.upper() if secondary_key else None,
            pollutant_values=pollutants,
            explanation=explanation
        )

    @staticmethod
    def compute_trend_intelligence(db: Session, location_id: Optional[int] = None) -> TrendIntelligence:
        """
        Analyzes chronological prediction history to evaluate trajectory and percentage shift.
        """
        query = db.query(Prediction).order_by(desc(Prediction.prediction_time))
        if location_id is not None:
            query = query.filter(Prediction.location_id == location_id)

        recent_records = query.limit(10).all()

        if len(recent_records) < 2:
            return TrendIntelligence(
                direction="insufficient_data",
                percentage_change=None,
                explanation="Insufficient historical predictions recorded to evaluate meaningful atmospheric trend."
            )

        latest_aqi = recent_records[0].predicted_aqi
        older_aqi = recent_records[-1].predicted_aqi

        if older_aqi <= 0:
            diff_pct = 0.0
        else:
            diff_pct = round(((latest_aqi - older_aqi) / older_aqi) * 100.0, 1)

        diff = latest_aqi - older_aqi
        if diff > 5.0:
            direction = "worsening"
            explanation = f"Air quality has deteriorated by {abs(diff_pct)}% over the recent observation window (AQI increased from {older_aqi:.1f} to {latest_aqi:.1f})."
        elif diff < -5.0:
            direction = "improving"
            explanation = f"Air quality is improving with an AQI reduction of {abs(diff_pct)}% (decreased from {older_aqi:.1f} to {latest_aqi:.1f})."
        else:
            direction = "stable"
            explanation = f"Air quality remains stable around AQI {latest_aqi:.1f} with negligible fluctuation ({diff_pct:+0.1f}%)."

        return TrendIntelligence(
            direction=direction,
            percentage_change=diff_pct,
            explanation=explanation
        )

    @staticmethod
    def generate_health_and_env_advice(aqi: float, weather: Dict[str, Optional[float]]) -> Tuple[str, List[str], List[str], List[str]]:
        """
        Generates risk level, actionable health guidance, environmental factor explanations, and recommendations.
        """
        category, _, _ = get_aqi_category_info(aqi)

        if aqi <= 50:
            risk = "Low Risk"
            health = [
                "Air quality is clean and satisfactory for all population groups.",
                "Ideal conditions for outdoor sports, exercise, and ventilation."
            ]
            recs = [
                "Enjoy unrestricted outdoor activities.",
                "Open windows for natural home and office ventilation."
            ]
        elif aqi <= 100:
            risk = "Moderate Risk"
            health = [
                "Air quality is acceptable for the general public.",
                "Individuals with extreme respiratory sensitivity may experience mild irritation."
            ]
            recs = [
                "Sensitive individuals should consider reducing prolonged heavy outdoor exertion.",
                "Keep inhalers handy if diagnosed with asthma or bronchial conditions."
            ]
        elif aqi <= 200:
            risk = "Elevated Risk"
            health = [
                "Members of sensitive groups (children, elderly, respiratory patients) may experience health effects.",
                "General public is less likely to be acutely affected but may experience eye/throat irritation."
            ]
            recs = [
                "Wear an N95 or particulate mask when commuting in congested traffic.",
                "Shift high-intensity cardio and running workouts indoors.",
                "Run indoor HEPA air purifiers if available."
            ]
        else:
            risk = "High / Hazardous Risk"
            health = [
                "Health alert: Everyone may experience serious health effects from particulate exposure.",
                "Significant risk of respiratory distress and cardiovascular stress."
            ]
            recs = [
                "Avoid all prolonged outdoor physical activity.",
                "Keep windows tightly closed and activate indoor air filtration.",
                "Follow municipal environmental emergency guidelines."
            ]

        # Environmental factors breakdown
        temp = weather.get("temperature")
        wind = weather.get("wind_speed")
        humidity = weather.get("humidity")
        env_factors = []

        if wind is not None:
            if wind < 4.0:
                env_factors.append(f"Low wind speed ({wind} km/h) creates stagnant air conditions, causing particulate matter to accumulate near ground level.")
            else:
                env_factors.append(f"Moderate wind speed ({wind} km/h) aids horizontal ventilation and dispersion of atmospheric pollutants.")

        if humidity is not None and humidity > 70.0:
            env_factors.append(f"High relative humidity ({humidity}%) can promote secondary aerosol formation and particulate hygroscopic growth.")

        if temp is not None:
            env_factors.append(f"Ambient temperature of {temp}°C influences atmospheric mixing layer depth.")

        return risk, health, env_factors, recs

    @staticmethod
    def generate_smart_alerts(
        db: Session,
        current_aqi: Optional[float] = None,
        pollutants: Optional[Dict[str, Optional[float]]] = None,
        location_id: Optional[int] = None
    ) -> List[SmartAlert]:
        """
        Generates actionable, threshold-driven smart notifications based on current metrics and trend.
        """
        alerts = []
        now = datetime.now(timezone.utc)

        # 1. AQI Threshold Alert
        if current_aqi is not None:
            if current_aqi > 200:
                alerts.append(
                    SmartAlert(
                        severity="danger",
                        title="Severe Air Quality Warning",
                        message=f"Current AQI ({current_aqi:.1f}) is in the Very Unhealthy/Hazardous tier. Minimize outdoor exposure immediately.",
                        timestamp=now
                    )
                )
            elif current_aqi > 100:
                alerts.append(
                    SmartAlert(
                        severity="warning",
                        title="Air Quality Advisory for Sensitive Groups",
                        message=f"AQI ({current_aqi:.1f}) is elevated. Children, elderly, and individuals with respiratory conditions should limit exertion.",
                        timestamp=now
                    )
                )

        # 2. Particulate Matter Specific Spikes
        if pollutants:
            pm25 = pollutants.get("pm25")
            pm10 = pollutants.get("pm10")

            if pm25 is not None and pm25 > 60.0:
                alerts.append(
                    SmartAlert(
                        severity="warning",
                        title="Elevated PM2.5 Concentration",
                        message=f"Fine particulate matter (PM2.5) is high at {pm25} µg/m³. N95 masks recommended near heavy traffic.",
                        timestamp=now
                    )
                )

            if pm10 is not None and pm10 > 100.0:
                alerts.append(
                    SmartAlert(
                        severity="info",
                        title="Dust & Coarse Particulate Alert",
                        message=f"PM10 level is currently {pm10} µg/m³, indicating potential road dust, windblown particles, or construction activity.",
                        timestamp=now
                    )
                )

        # 3. Sudden Trend Surge Alert
        trend = AIInsightEngine.compute_trend_intelligence(db, location_id)
        if trend.direction == "worsening" and trend.percentage_change and trend.percentage_change > 15.0:
            alerts.append(
                SmartAlert(
                    severity="warning",
                    title="Rapid Air Quality Deterioration",
                    message=f"Air pollution has surged by {trend.percentage_change}% recently. Take proactive exposure reduction measures.",
                    timestamp=now
                )
            )

        if not alerts:
            alerts.append(
                SmartAlert(
                    severity="info",
                    title="Normal Atmospheric State",
                    message="All ambient air quality and meteorological metrics are currently within nominal seasonal baselines.",
                    timestamp=now
                )
            )

        return alerts

    @staticmethod
    def get_full_insights(
        db: Session,
        location_id: Optional[int] = None
    ) -> AIInsightsResponse:
        """
        Orchestrates complete AI insight response combining ML predictions, dominant pollutant parsing,
        meteorological dispersion factors, and trend intelligence.
        """
        # Fetch latest recorded prediction and associated readings
        pred_query = db.query(Prediction, Location).join(Location, Prediction.location_id == Location.id)
        if location_id is not None:
            pred_query = pred_query.filter(Prediction.location_id == location_id)

        latest_record = pred_query.order_by(desc(Prediction.prediction_time)).first()

        if not latest_record:
            return AIInsightsResponse(
                success=True,
                current_aqi=None,
                aqi_category="No Data",
                risk_level="Unknown",
                summary="No recent air quality observations are available in the system ledger. Please submit a prediction or select a location.",
                dominant_pollutants=DominantPollutantAnalysis(
                    dominant_pollutant="N/A",
                    secondary_pollutant=None,
                    pollutant_values={},
                    explanation="No telemetry available to compute pollutant dominance."
                ),
                health_advice=["Run a prediction query above to receive personalized advice."],
                environmental_factors=["Awaiting meteorological data."],
                trend=TrendIntelligence(
                    direction="insufficient_data",
                    percentage_change=None,
                    explanation="Insufficient historical predictions."
                ),
                recommendations=["Select your coordinates on the dashboard to compute real-time insights."]
            )

        pred, loc = latest_record
        aqi = float(round(pred.predicted_aqi, 2))
        category, _, _ = get_aqi_category_info(aqi)

        # Retrieve associated telemetry
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

        dom_analysis = AIInsightEngine.analyze_dominant_pollutants(pollutants)
        trend_info = AIInsightEngine.compute_trend_intelligence(db, location_id=loc.id)
        risk, health_advice, env_factors, recommendations = AIInsightEngine.generate_health_and_env_advice(aqi, weather)

        summary = (
            f"The GradientBoostingRegressor ML model predicts an Air Quality Index of {aqi} ({category} - {risk}) for {loc.city}. "
            f"{dom_analysis.explanation} {trend_info.explanation}"
        )

        return AIInsightsResponse(
            success=True,
            current_aqi=aqi,
            aqi_category=category,
            risk_level=risk,
            summary=summary,
            dominant_pollutants=dom_analysis,
            health_advice=health_advice,
            environmental_factors=env_factors,
            trend=trend_info,
            recommendations=recommendations,
            model_provenance="GradientBoostingRegressor (models/best_model.joblib)",
            timestamp=pred.prediction_time
        )
