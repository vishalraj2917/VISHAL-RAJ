import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import get_db
from app.routers.prediction import router as prediction_router
from app.routers.ai_features import router as ai_router
from app.routers.analytics import router as analytics_router
from app.routers.insights import router as insights_router
from app.routers.auth import router as auth_router
from app.services.prediction_service import PredictionService

# Configure logging
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aqi_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly load ML model and preprocessor into memory on startup
    logger.info(f"Starting AI Air Quality Prediction API in {settings.ENVIRONMENT} mode...")
    try:
        service = PredictionService.get_instance()
        if service.is_ready():
            logger.info("ML champion model & preprocessor loaded into memory.")
    except Exception as e:
        logger.error(f"Failed to load ML artifacts at startup: {e}")
    yield
    logger.info("Application shutdown complete.")


app = FastAPI(
    title='AI Air Quality Prediction API',
    description='Production FastAPI backend with integrated ML inference, AI features, historical analytics, and secure user authentication for AI Air Quality Prediction System',
    version='1.0.0',
    docs_url='/docs' if settings.ENABLE_DOCS else None,
    redoc_url='/redoc' if settings.ENABLE_DOCS else None,
    lifespan=lifespan,
)

# Request Timing & Access Logger Middleware
@app.middleware("http")
async def log_requests_and_timing(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        return response
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"{request.method} {request.url.path} -> 500 Unhandled Exception ({duration_ms}ms): {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "detail": "An internal server error occurred. Please contact the system administrator."
            }
        )

# Configurable CORS with full preflight OPTIONS support for all local development ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register API routers
app.include_router(auth_router)
app.include_router(prediction_router)
app.include_router(ai_router)
app.include_router(analytics_router)
app.include_router(insights_router)


@app.get('/')
def root():
    return {
        'message': 'AI Air Quality Prediction System API is running.',
        'version': '1.0.0',
        'environment': settings.ENVIRONMENT,
        'docs_url': '/docs' if settings.ENABLE_DOCS else None
    }


@app.get('/api/health')
def health_check(db: Session = Depends(get_db)):
    """
    Liveness probe: verifies basic service responsiveness and dependency status.
    """
    try:
        db.execute(text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = 'disconnected'
        logger.warning(f"Database health check query failed: {e}")

    try:
        service = PredictionService.get_instance()
        ml_status = 'ready' if service.is_ready() else 'unavailable'
        model_name = service.metadata.get("model_name", "Unknown")
    except Exception:
        ml_status = 'error'
        model_name = None

    is_healthy = (db_status == 'connected') and (ml_status == 'ready')

    response_payload = {
        'status': 'ok' if is_healthy else 'degraded',
        'database': db_status,
        'ml_model': ml_status,
        'model_name': model_name,
    }

    if not is_healthy and db_status == 'disconnected':
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response_payload
        )

    return response_payload


@app.get('/api/ready')
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe: validates that database connection, ML model, and preprocessor are ready for traffic.
    """
    db_ok = False
    try:
        db.execute(text('SELECT 1'))
        db_ok = True
    except Exception as e:
        logger.error(f"Readiness check database failure: {e}")

    ml_ok = False
    try:
        service = PredictionService.get_instance()
        ml_ok = service.is_ready()
    except Exception as e:
        logger.error(f"Readiness check ML service failure: {e}")

    if not (db_ok and ml_ok):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "ok" if db_ok else "unavailable",
                "ml_model": "ok" if ml_ok else "unavailable"
            }
        )

    return {
        "status": "ready",
        "database": "ok",
        "ml_model": "ok"
    }
