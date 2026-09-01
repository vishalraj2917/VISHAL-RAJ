import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ai import (
    AIChatRequest,
    AIChatResponse,
    AIReportRequest,
    AIReportResponse,
    AIHealthAdviceRequest,
    AIHealthAdviceResponse,
)
from app.schemas.ai_insights import (
    AIInsightsResponse,
    SmartAlertsResponse,
)
from app.services.ai_service import AIService, get_ai_service
from app.services.ai_insight_service import AIInsightEngine

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ai",
    tags=["AI Features & Insights"]
)


@router.post(
    "/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Air Quality Chatbot",
    description="Conversational AI assistant answering questions about air pollution, safety recommendations, and telemetry interpretation.",
)
async def chat_with_ai(
    request: AIChatRequest,
    ai_service: AIService = Depends(get_ai_service),
):
    """
    Handles conversational interactions with contextual environmental awareness.
    """
    try:
        reply = await ai_service.generate_chat_reply(
            message=request.message,
            context=request.context,
            history=request.history,
        )
        return AIChatResponse(
            success=True,
            reply=reply,
            context_used=request.context is not None,
        )
    except Exception as e:
        logger.error(f"Error in AI chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI_SERVICE_UNAVAILABLE: Failed to process chat request."
        )


@router.post(
    "/report",
    response_model=AIReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Air Quality Report",
    description="Synthesizes live environmental metrics and ML predictions into a structured analytical report.",
)
async def generate_ai_report(
    request: AIReportRequest,
    ai_service: AIService = Depends(get_ai_service),
):
    """
    Produces executive air quality analysis and actionable safety recommendations.
    """
    try:
        report_sections = await ai_service.generate_report(request.context)
        return AIReportResponse(
            success=True,
            report=report_sections,
        )
    except Exception as e:
        logger.error(f"Error in AI report endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI_SERVICE_UNAVAILABLE: Failed to synthesize air quality report."
        )


@router.post(
    "/health-advice",
    response_model=AIHealthAdviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Personalized Health & Activity Advisor",
    description="Provides preventive health guidance tailored to specific activities and audience groups based on predicted AQI.",
)
async def generate_health_advice(
    request: AIHealthAdviceRequest,
    ai_service: AIService = Depends(get_ai_service),
):
    """
    Generates preventive activity advice without diagnosing medical conditions.
    """
    try:
        advice_data = await ai_service.generate_health_advice(
            activity=request.activity,
            target_group=request.target_group or "General Public",
            context=request.context,
        )
        return AIHealthAdviceResponse(
            success=True,
            activity=request.activity,
            target_group=request.target_group or "General Public",
            aqi_level=request.context.predicted_aqi,
            safety_rating=advice_data["safety_rating"],
            advice=advice_data["advice"],
            recommended_precautions=advice_data["recommended_precautions"],
        )
    except Exception as e:
        logger.error(f"Error in AI health advice endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI_SERVICE_UNAVAILABLE: Failed to generate health advisory."
        )


@router.get(
    "/insights",
    response_model=AIInsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI-Powered Air Quality Insights",
    description="Returns comprehensive AI interpretation including dominant pollutant analysis, health risk level, and trend intelligence.",
)
def get_ai_insights(
    location_id: Optional[int] = Query(None, description="Optional location filter ID"),
    db: Session = Depends(get_db),
):
    """
    Provides deterministic and model-aligned AI insights for current and historical air quality conditions.
    """
    try:
        return AIInsightEngine.get_full_insights(db, location_id=location_id)
    except Exception as e:
        logger.error(f"Error generating AI insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI air quality insights."
        )


@router.get(
    "/alerts",
    response_model=SmartAlertsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Smart Air Quality Alerts",
    description="Returns active threshold-driven and sudden-surge alerts for current conditions.",
)
def get_smart_alerts(
    location_id: Optional[int] = Query(None, description="Optional location filter ID"),
    db: Session = Depends(get_db),
):
    """
    Generates smart environmental notifications based on current AQI thresholds and trajectory.
    """
    try:
        insights = AIInsightEngine.get_full_insights(db, location_id=location_id)
        pollutant_vals = insights.dominant_pollutants.pollutant_values if insights.dominant_pollutants else {}
        alerts = AIInsightEngine.generate_smart_alerts(
            db=db,
            current_aqi=insights.current_aqi,
            pollutants=pollutant_vals,
            location_id=location_id
        )
        return SmartAlertsResponse(
            success=True,
            count=len(alerts),
            alerts=alerts
        )
    except Exception as e:
        logger.error(f"Error fetching smart alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate smart air quality alerts."
        )
