from app.routers.prediction import router as prediction_router
from app.routers.ai_features import router as ai_router
from app.routers.analytics import router as analytics_router
from app.routers.insights import router as insights_router
from app.routers.auth import router as auth_router

__all__ = [
    "prediction_router",
    "ai_router",
    "analytics_router",
    "insights_router",
    "auth_router",
]
