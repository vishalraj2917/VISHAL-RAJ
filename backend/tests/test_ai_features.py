import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.services.ai_service import AIService
from app.schemas.ai import (
    EnvironmentalContext,
    AIChatRequest,
    AIReportRequest,
    AIHealthAdviceRequest,
    AIReportSections,
)
from app.services.analytics_service import AnalyticsService

# Create in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_context():
    return {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "city_name": "Bengaluru",
        "predicted_aqi": 68.5,
        "aqi_category": "Moderate",
        "dominant_pollutant": "PM2.5",
        "pm25": 28.4,
        "pm10": 55.2,
        "co": 0.5,
        "no2": 18.2,
        "so2": 8.1,
        "o3": 25.0,
        "temperature": 27.5,
        "humidity": 60.0,
        "wind_speed": 4.5,
        "pressure": 1012.0,
        "observed_at": "2026-09-01T14:00",
    }


def test_ai_chat_success(client, sample_context):
    payload = {
        "message": "Is it safe to exercise outdoors today?",
        "context": sample_context,
    }
    response = client.post("/api/ai/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "reply" in data
    assert len(data["reply"]) > 10
    assert data["context_used"] is True
    assert "medical advice" in data["disclaimer"].lower()


def test_ai_chat_empty_message_rejected(client):
    response = client.post("/api/ai/chat", json={"message": "   "})
    assert response.status_code == 422


def test_ai_chat_oversized_message_rejected(client):
    oversized = "a" * 2500
    response = client.post("/api/ai/chat", json={"message": oversized})
    assert response.status_code == 422


def test_ai_chat_without_context(client):
    response = client.post("/api/ai/chat", json={"message": "What is PM2.5?"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "PM2.5" in data["reply"]
    assert data["context_used"] is False


def test_ai_report_generation(client, sample_context):
    payload = {
        "context": sample_context
    }
    response = client.post("/api/ai/report", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "report" in data
    assert "summary" in data["report"]
    assert "air_quality_analysis" in data["report"]
    assert "weather_impact" in data["report"]
    assert isinstance(data["report"]["safety_recommendations"], list)
    assert len(data["report"]["safety_recommendations"]) > 0


def test_ai_health_advice_generation(client, sample_context):
    payload = {
        "activity": "Outdoor Exercise",
        "target_group": "General Public",
        "context": sample_context,
    }
    response = client.post("/api/ai/health-advice", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["activity"] == "Outdoor Exercise"
    assert data["safety_rating"] in ["Safe", "Caution", "Unfavorable"]
    assert "advice" in data
    assert isinstance(data["recommended_precautions"], list)
    assert "healthcare professional" in data["disclaimer"].lower()


def test_ai_service_llm_mocking(client, sample_context):
    mock_reply = "Mocked AI response explaining environmental conditions perfectly."

    with patch.object(AIService, "generate_chat_reply", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_reply

        response = client.post("/api/ai/chat", json={
            "message": "Tell me about air quality",
            "context": sample_context
        })
        assert response.status_code == 200
        assert response.json()["reply"] == mock_reply


def test_ai_insights_endpoint_empty_and_populated(client):
    # 1. Empty state
    res_empty = client.get("/api/ai/insights")
    assert res_empty.status_code == 200
    data_empty = res_empty.json()
    assert data_empty["success"] is True
    assert data_empty["current_aqi"] is None
    assert "insufficient_data" in data_empty["trend"]["direction"]

    # 2. Add prediction
    pred_payload = {
        "pm25": 45.2,
        "pm10": 85.0,
        "co": 0.8,
        "no2": 24.5,
        "so2": 11.2,
        "o3": 28.0,
        "temperature": 27.5,
        "humidity": 62.0,
        "wind_speed": 3.8,
        "pressure": 1012.5,
        "hour": 14,
        "day": 15,
        "month": 6,
        "day_of_week": 2,
        "is_weekend": 0
    }
    client.post("/api/predict", json=pred_payload)

    # 3. Populated state
    res_pop = client.get("/api/ai/insights")
    assert res_pop.status_code == 200
    data_pop = res_pop.json()
    assert data_pop["current_aqi"] > 0
    assert data_pop["dominant_pollutants"]["dominant_pollutant"] is not None
    assert len(data_pop["health_advice"]) > 0
    assert len(data_pop["recommendations"]) > 0


def test_smart_alerts_generation(client):
    # Get alerts initially
    res = client.get("/api/ai/alerts")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["alerts"]) > 0
    assert data["alerts"][0]["severity"] in ["info", "warning", "danger"]
