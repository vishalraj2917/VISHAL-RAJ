import logging
from typing import Optional
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    LivePredictionRequest,
    LivePredictionResponse,
    LocationCoordinates,
    LivePollutantData,
    LiveWeatherData,
    ModelInfo,
)
from app.services.prediction_service import PredictionService, get_prediction_service
from app.services.weather_service import WeatherService
from app.services.air_quality_service import AirQualityService
from app.services.live_feature_service import LiveFeatureService
from app.services.analytics_service import AnalyticsService
from app.utils.security import get_current_user_optional
from app.models.models import Prediction, Location, AirQuality, Weather, User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Prediction"]
)


def get_weather_service() -> WeatherService:
    return WeatherService()


def get_air_quality_service() -> AirQualityService:
    return AirQualityService()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Air Quality Index (AQI)",
    description="Accepts ambient pollutant measurements and weather features, validates physical ranges, and returns machine learning AQI prediction.",
    responses={
        200: {
            "description": "Successful AQI prediction",
            "model": PredictionResponse
        },
        422: {
            "description": "Validation Error - Missing, out-of-range, NaN, or invalid input parameters"
        },
        500: {
            "description": "Internal Server Error / Model Unavailable"
        }
    }
)
def predict_aqi(
    request: PredictionRequest,
    service: PredictionService = Depends(get_prediction_service),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Computes continuous AQI from input features using the champion Gradient Boosting model.
    Stores prediction and observation history linked to authenticated user.
    """
    try:
        response = service.predict_single(request)

        # Automatic history persistence in PostgreSQL (with user_id if authenticated)
        try:
            pollutants = {
                "pm25": request.pm25,
                "pm10": request.pm10,
                "co": request.co,
                "no2": request.no2,
                "so2": request.so2,
                "o3": request.o3,
            }
            weather_data = {
                "temperature": request.temperature,
                "humidity": request.humidity,
                "wind_speed": request.wind_speed,
                "pressure": request.pressure,
            }
            AnalyticsService.record_prediction(
                db=db,
                predicted_aqi=response.prediction.aqi,
                model_name=response.model.name,
                user_id=current_user.id if current_user else None,
                pollutants=pollutants,
                weather_data=weather_data,
                timestamp=response.timestamp,
            )
        except Exception as db_err:
            db.rollback()
            logger.warning(f"Failed to record prediction in DB history: {db_err}")

        return response

    except RuntimeError as e:
        logger.error(f"Prediction runtime error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Machine learning model prediction service is currently unavailable."
        )
    except Exception as e:
        logger.error(f"Unexpected prediction failure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the air quality prediction."
        )


@router.post(
    "/predict/live",
    response_model=LivePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict AQI from Live Environmental Data",
    description="Fetches live meteorological and pollutant metrics for given latitude and longitude, constructs 21 ML features, and predicts continuous AQI.",
    responses={
        200: {
            "description": "Successful live environmental AQI prediction",
            "model": LivePredictionResponse
        },
        422: {
            "description": "Validation Error - Invalid coordinates"
        },
        502: {
            "description": "Bad Gateway - External Live Weather or Air Quality API unavailable or timed out"
        },
        500: {
            "description": "Internal Server Error / Model Unavailable"
        }
    }
)
async def predict_live_aqi(
    request: LivePredictionRequest,
    prediction_service: PredictionService = Depends(get_prediction_service),
    weather_service: WeatherService = Depends(get_weather_service),
    air_quality_service: AirQualityService = Depends(get_air_quality_service),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Fetches live weather and air quality via external APIs and runs ML prediction.
    """
    lat, lon = request.latitude, request.longitude

    # 1. Fetch live external APIs concurrently
    try:
        weather_task = weather_service.fetch_current_weather(lat, lon)
        aq_task = air_quality_service.fetch_current_air_quality(lat, lon)
        weather_data, aq_data = await asyncio.gather(weather_task, aq_task)

    except (TimeoutError, ConnectionError) as e:
        logger.error(f"External API connectivity failure for ({lat}, {lon}): {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LIVE_DATA_UNAVAILABLE: External meteorological or air quality data provider is temporarily unavailable or timed out."
        )
    except (ValueError, PermissionError, RuntimeError) as e:
        logger.error(f"External API parsing / permission error for ({lat}, {lon}): {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LIVE_DATA_UNAVAILABLE: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching live external data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LIVE_DATA_UNAVAILABLE: Failed to acquire real-time environmental observations."
        )

    # 2. Build and validate 21 ML features
    try:
        pred_req, raw_features = LiveFeatureService.build_features(
            air_quality=aq_data,
            weather=weather_data,
            location_id=request.location_id
        )
    except Exception as e:
        logger.error(f"Error engineering features from live data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute normalized ML features from live data."
        )

    # 3. Predict AQI using ML pipeline
    try:
        pred_res = prediction_service.predict_single(pred_req)
    except Exception as e:
        logger.error(f"ML prediction error on live features: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Machine learning prediction failed on live input features."
        )

    # 4. Database persistence with user isolation
    try:
        obs_dt = LiveFeatureService.parse_observation_time(
            weather_data.get("timestamp"),
            weather_data.get("timezone")
        )
        AnalyticsService.record_prediction(
            db=db,
            predicted_aqi=pred_res.prediction.aqi,
            model_name=pred_res.model.name,
            user_id=current_user.id if current_user else None,
            latitude=lat,
            longitude=lon,
            pollutants=aq_data,
            weather_data=weather_data,
            timestamp=obs_dt,
        )
    except Exception as db_err:
        db.rollback()
        logger.warning(f"Failed to persist live prediction in database: {db_err}")

    # 5. Format and return response
    return LivePredictionResponse(
        success=True,
        location=LocationCoordinates(latitude=lat, longitude=lon),
        air_quality=LivePollutantData(
            pm25=aq_data["pm25"],
            pm10=aq_data["pm10"],
            co=aq_data["co"],
            no2=aq_data["no2"],
            so2=aq_data["so2"],
            o3=aq_data["o3"],
        ),
        weather=LiveWeatherData(
            temperature=weather_data["temperature"],
            humidity=weather_data["humidity"],
            wind_speed=weather_data["wind_speed"],
            pressure=weather_data["pressure"],
        ),
        prediction=pred_res.prediction,
        model=pred_res.model,
        observed_at=str(weather_data.get("timestamp") or aq_data.get("timestamp")),
        timestamp=pred_res.timestamp,
    )


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch Predict Air Quality Index (AQI)",
    description="Vectorized predictions for multiple records (up to 100 observations).",
)
def predict_aqi_batch(
    request: BatchPredictionRequest,
    service: PredictionService = Depends(get_prediction_service),
):
    try:
        return service.predict_batch(request)
    except RuntimeError as e:
        logger.error(f"Batch prediction runtime error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Machine learning model prediction service is currently unavailable."
        )
    except Exception as e:
        logger.error(f"Unexpected batch prediction failure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while computing batch predictions."
        )


@router.get(
    "/model/info",
    response_model=ModelInfo,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Active ML Model Information",
    description="Returns metadata, architecture, features, and validated metrics for the deployed champion model.",
)
def get_active_model_info(
    service: PredictionService = Depends(get_prediction_service),
):
    return service.get_model_info()
