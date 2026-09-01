import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.models.models import Prediction, Location, AirQuality, Weather, User
from app.services.prediction_service import get_aqi_category_info
from app.schemas.analytics import (
    PredictionHistoryItem,
    PredictionHistoryResponse,
    AnalyticsSummaryResponse,
    TrendPoint,
    AnalyticsTrendsResponse,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analytics & Prediction History database retrieval service.
    Computes statistical aggregations, trend trajectory, and chronological time series with User isolation.
    """

    @staticmethod
    def get_or_create_location(
        db: Session,
        latitude: float,
        longitude: float,
        city: Optional[str] = None
    ) -> Location:
        """
        Locates an existing Location record or creates a new one based on coordinates.
        """
        loc = db.query(Location).filter(
            func.abs(Location.latitude - latitude) < 0.05,
            func.abs(Location.longitude - longitude) < 0.05
        ).first()

        if loc is None:
            loc = Location(
                city=city or f"Station ({round(latitude, 2)}, {round(longitude, 2)})",
                latitude=latitude,
                longitude=longitude,
                country="India"
            )
            db.add(loc)
            db.commit()
            db.refresh(loc)
        return loc

    @staticmethod
    def record_prediction(
        db: Session,
        predicted_aqi: float,
        model_name: str,
        user_id: Optional[int] = None,
        latitude: float = 12.9716,
        longitude: float = 77.5946,
        city: Optional[str] = None,
        pollutants: Optional[Dict[str, Any]] = None,
        weather_data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> Prediction:
        """
        Stores prediction, telemetry, and weather observations in PostgreSQL linked to user_id if provided.
        """
        ts = timestamp or datetime.now(timezone.utc)
        location = AnalyticsService.get_or_create_location(db, latitude, longitude, city)

        # 1. Store Prediction record
        pred = Prediction(
            user_id=user_id,
            location_id=location.id,
            prediction_time=ts,
            predicted_aqi=float(predicted_aqi),
            model_name=model_name,
            created_at=datetime.now(timezone.utc)
        )
        db.add(pred)

        # 2. Store AirQuality observation if provided
        if pollutants:
            aq = AirQuality(
                location_id=location.id,
                timestamp=ts,
                pm25=float(pollutants.get("pm25")) if pollutants.get("pm25") is not None else None,
                pm10=float(pollutants.get("pm10")) if pollutants.get("pm10") is not None else None,
                co=float(pollutants.get("co")) if pollutants.get("co") is not None else None,
                no2=float(pollutants.get("no2")) if pollutants.get("no2") is not None else None,
                so2=float(pollutants.get("so2")) if pollutants.get("so2") is not None else None,
                o3=float(pollutants.get("o3")) if pollutants.get("o3") is not None else None,
                aqi=float(predicted_aqi),
            )
            db.add(aq)

        # 3. Store Weather observation if provided
        if weather_data:
            w = Weather(
                location_id=location.id,
                timestamp=ts,
                temperature=float(weather_data.get("temperature")) if weather_data.get("temperature") is not None else None,
                humidity=float(weather_data.get("humidity")) if weather_data.get("humidity") is not None else None,
                wind_speed=float(weather_data.get("wind_speed")) if weather_data.get("wind_speed") is not None else None,
                pressure=float(weather_data.get("pressure")) if weather_data.get("pressure") is not None else None,
            )
            db.add(w)

        db.commit()
        db.refresh(pred)
        return pred

    @staticmethod
    def get_history(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        location_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> PredictionHistoryResponse:
        """
        Fetches paginated list of prediction history joined with location and telemetry.
        Filters by user_id for strict account isolation if requested.
        """
        query = db.query(Prediction, Location).join(Location, Prediction.location_id == Location.id)
        if user_id is not None:
            query = query.filter(Prediction.user_id == user_id)
        if location_id is not None:
            query = query.filter(Prediction.location_id == location_id)

        total_count = query.count()
        records = query.order_by(desc(Prediction.prediction_time)).offset(offset).limit(limit).all()

        history_items = []
        for pred, loc in records:
            category, color, _ = get_aqi_category_info(pred.predicted_aqi)

            aq = db.query(AirQuality).filter(
                AirQuality.location_id == loc.id,
                AirQuality.timestamp == pred.prediction_time
            ).first()

            w = db.query(Weather).filter(
                Weather.location_id == loc.id,
                Weather.timestamp == pred.prediction_time
            ).first()

            history_items.append(
                PredictionHistoryItem(
                    id=pred.id,
                    timestamp=pred.prediction_time,
                    predicted_aqi=float(round(pred.predicted_aqi, 2)),
                    aqi_category=category,
                    color=color,
                    model_name=pred.model_name,
                    location_id=loc.id,
                    city=loc.city,
                    latitude=loc.latitude,
                    longitude=loc.longitude,
                    pm25=aq.pm25 if aq else None,
                    pm10=aq.pm10 if aq else None,
                    co=aq.co if aq else None,
                    no2=aq.no2 if aq else None,
                    so2=aq.so2 if aq else None,
                    o3=aq.o3 if aq else None,
                    temperature=w.temperature if w else None,
                    humidity=w.humidity if w else None,
                    wind_speed=w.wind_speed if w else None,
                    pressure=w.pressure if w else None,
                )
            )

        return PredictionHistoryResponse(
            success=True,
            count=len(history_items),
            total=total_count,
            history=history_items
        )

    @staticmethod
    def get_latest_prediction(
        db: Session,
        location_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Optional[PredictionHistoryItem]:
        history_resp = AnalyticsService.get_history(db, limit=1, offset=0, location_id=location_id, user_id=user_id)
        if history_resp.history:
            return history_resp.history[0]
        return None

    @staticmethod
    def get_summary(
        db: Session,
        location_id: Optional[int] = None,
        user_id: Optional[int] = None,
        hours: int = 720
    ) -> AnalyticsSummaryResponse:
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = db.query(Prediction).filter(Prediction.prediction_time >= since_time)
        if user_id is not None:
            query = query.filter(Prediction.user_id == user_id)
        if location_id is not None:
            query = query.filter(Prediction.location_id == location_id)

        preds = query.order_by(desc(Prediction.prediction_time)).all()

        if not preds:
            return AnalyticsSummaryResponse(
                success=True,
                current_aqi=None,
                current_category=None,
                current_color=None,
                average_aqi=0.0,
                min_aqi=0.0,
                max_aqi=0.0,
                total_predictions=0,
                trend_direction="stable",
                most_recent_timestamp=None
            )

        aqi_values = [p.predicted_aqi for p in preds]
        latest_pred = preds[0]
        latest_aqi = float(round(latest_pred.predicted_aqi, 2))
        latest_cat, latest_color, _ = get_aqi_category_info(latest_aqi)

        avg_aqi = float(round(sum(aqi_values) / len(aqi_values), 2))
        min_aqi = float(round(min(aqi_values), 2))
        max_aqi = float(round(max(aqi_values), 2))

        trend = "stable"
        if len(preds) >= 2:
            first = preds[-1].predicted_aqi
            last = preds[0].predicted_aqi
            diff = last - first
            if diff > 5.0:
                trend = "deteriorating"
            elif diff < -5.0:
                trend = "improving"

        return AnalyticsSummaryResponse(
            success=True,
            current_aqi=latest_aqi,
            current_category=latest_cat,
            current_color=latest_color,
            average_aqi=avg_aqi,
            min_aqi=min_aqi,
            max_aqi=max_aqi,
            total_predictions=len(preds),
            trend_direction=trend,
            most_recent_timestamp=latest_pred.prediction_time
        )

    @staticmethod
    def get_trends(
        db: Session,
        hours: int = 168,
        location_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> AnalyticsTrendsResponse:
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = db.query(Prediction, Location).join(Location, Prediction.location_id == Location.id)\
            .filter(Prediction.prediction_time >= since_time)

        if user_id is not None:
            query = query.filter(Prediction.user_id == user_id)
        if location_id is not None:
            query = query.filter(Prediction.location_id == location_id)

        records = query.order_by(Prediction.prediction_time.asc()).limit(200).all()

        points = []
        for pred, loc in records:
            cat, _, _ = get_aqi_category_info(pred.predicted_aqi)

            aq = db.query(AirQuality).filter(
                AirQuality.location_id == loc.id,
                AirQuality.timestamp == pred.prediction_time
            ).first()

            w = db.query(Weather).filter(
                Weather.location_id == loc.id,
                Weather.timestamp == pred.prediction_time
            ).first()

            points.append(
                TrendPoint(
                    timestamp=pred.prediction_time,
                    aqi=float(round(pred.predicted_aqi, 2)),
                    category=cat,
                    pm25=aq.pm25 if aq else None,
                    pm10=aq.pm10 if aq else None,
                    no2=aq.no2 if aq else None,
                    o3=aq.o3 if aq else None,
                    temperature=w.temperature if w else None,
                    humidity=w.humidity if w else None,
                )
            )

        return AnalyticsTrendsResponse(
            success=True,
            period_hours=hours,
            points_count=len(points),
            trends=points
        )
