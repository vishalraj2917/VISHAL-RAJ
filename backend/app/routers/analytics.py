import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import (
    PredictionHistoryItem,
    PredictionHistoryResponse,
    AnalyticsSummaryResponse,
    AnalyticsTrendsResponse,
)
from app.services.analytics_service import AnalyticsService
from app.utils.security import get_current_user_optional
from app.models.models import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Analytics & History"]
)


@router.get(
    "/predictions/history",
    response_model=PredictionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Prediction History",
    description="Returns paginated list of historical ML predictions and recorded atmospheric parameters.",
)
def get_prediction_history(
    limit: int = Query(20, ge=1, le=100, description="Max number of records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    try:
        user_id = current_user.id if current_user else None
        return AnalyticsService.get_history(db, limit=limit, offset=offset, location_id=location_id, user_id=user_id)
    except Exception as e:
        logger.error(f"Error fetching prediction history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prediction history from database."
        )


@router.get(
    "/predictions/latest",
    response_model=Optional[PredictionHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Get Latest Prediction",
    description="Returns the most recent single prediction record.",
)
def get_latest_prediction(
    location_id: Optional[int] = Query(None, description="Optional location filter"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    try:
        user_id = current_user.id if current_user else None
        latest = AnalyticsService.get_latest_prediction(db, location_id=location_id, user_id=user_id)
        if latest is None:
            return None
        return latest
    except Exception as e:
        logger.error(f"Error fetching latest prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest prediction from database."
        )


@router.get(
    "/analytics/summary",
    response_model=AnalyticsSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Analytics Summary",
    description="Calculates current, average, min, and max AQI with trend direction over a time window.",
)
def get_analytics_summary(
    hours: int = Query(720, ge=1, le=8760, description="Time window in hours (default 720 = 30 days)"),
    location_id: Optional[int] = Query(None, description="Optional location filter"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    try:
        user_id = current_user.id if current_user else None
        return AnalyticsService.get_summary(db, location_id=location_id, user_id=user_id, hours=hours)
    except Exception as e:
        logger.error(f"Error calculating analytics summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute analytics summary metrics."
        )


@router.get(
    "/analytics/trends",
    response_model=AnalyticsTrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Analytics Trends",
    description="Returns chronological time-series data points for AQI and key pollutants over a specified period.",
)
def get_analytics_trends(
    hours: int = Query(168, ge=1, le=8760, description="Period in hours (e.g. 24, 168, 720)"),
    location_id: Optional[int] = Query(None, description="Optional location filter"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    try:
        user_id = current_user.id if current_user else None
        return AnalyticsService.get_trends(db, hours=hours, location_id=location_id, user_id=user_id)
    except Exception as e:
        logger.error(f"Error fetching analytics trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute chronological trend series."
        )
