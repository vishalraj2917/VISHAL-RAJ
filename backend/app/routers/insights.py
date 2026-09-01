import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.insights import InsightsRequest, InsightsResponse
from app.services.ai_insights_service import AIInsightsService
from app.services.prediction_service import PredictionService, get_prediction_service
from app.schemas.prediction import PredictionRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["AI Insights & Recommendations"]
)


@router.get(
    "/insights",
    response_model=InsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Air Quality Insights",
    description="Returns structured insights, category, risk level, pollutant contributions, and recommendations for latest system observation.",
)
def get_current_insights(
    location_id: Optional[int] = Query(None, description="Optional Location ID filter"),
    db: Session = Depends(get_db),
):
    try:
        return AIInsightsService.get_latest_system_insights(db, location_id=location_id)
    except Exception as e:
        logger.error(f"Error retrieving system insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate air quality insights."
        )


@router.post(
    "/insights",
    response_model=InsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Custom Air Quality Insights",
    description="Generates on-demand insights, risk assessment, and smart recommendations for custom pollutant and meteorological parameters.",
)
def generate_custom_insights(
    request: InsightsRequest,
    db: Session = Depends(get_db),
    prediction_service: PredictionService = Depends(get_prediction_service),
):
    try:
        # If AQI was not directly provided, compute it via ML model if required features exist
        aqi_val = request.aqi
        if aqi_val is None:
            # Fallback compute with defaults for missing features
            pred_req = PredictionRequest(
                pm25=request.pm25 if request.pm25 is not None else 45.0,
                pm10=request.pm10 if request.pm10 is not None else 80.0,
                co=request.co if request.co is not None else 0.8,
                no2=request.no2 if request.no2 is not None else 25.0,
                so2=request.so2 if request.so2 is not None else 10.0,
                o3=request.o3 if request.o3 is not None else 30.0,
                temperature=request.temperature if request.temperature is not None else 25.0,
                humidity=request.humidity if request.humidity is not None else 60.0,
                wind_speed=request.wind_speed if request.wind_speed is not None else 5.0,
                pressure=request.pressure if request.pressure is not None else 1013.0,
                hour=12,
                day=15,
                month=6,
                day_of_week=2,
                is_weekend=0,
            )
            pred_res = prediction_service.predict_single(pred_req)
            aqi_val = pred_res.prediction.aqi

        pollutants = {
            "pm25": request.pm25,
            "pm10": request.pm10,
            "co": request.co,
            "no2": request.no2,
            "so2": request.so2,
            "o3": request.o3,
        }

        weather = {
            "temperature": request.temperature,
            "humidity": request.humidity,
            "wind_speed": request.wind_speed,
            "pressure": request.pressure,
        }

        trend = AIInsightsService.calculate_historical_trend(db, location_id=request.location_id)

        return AIInsightsService.generate_insights_from_data(
            aqi=aqi_val,
            pollutants=pollutants,
            weather=weather,
            trend=trend,
            city_name=None
        )

    except Exception as e:
        logger.error(f"Error generating custom insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process custom air quality insights."
        )
