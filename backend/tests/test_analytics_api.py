import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.models import Prediction, Location, AirQuality, Weather
from app.services.analytics_service import AnalyticsService

# Create in-memory SQLite for testing analytics endpoints without external DB dependency
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
def sample_prediction_payload():
    return {
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


def test_empty_history_and_analytics(client):
    # Test history when no records exist
    res_hist = client.get("/api/predictions/history")
    assert res_hist.status_code == 200
    data_hist = res_hist.json()
    assert data_hist["success"] is True
    assert data_hist["count"] == 0
    assert data_hist["total"] == 0

    # Test latest prediction when none exist
    res_latest = client.get("/api/predictions/latest")
    assert res_latest.status_code == 200
    assert res_latest.json() is None

    # Test summary when empty
    res_summary = client.get("/api/analytics/summary")
    assert res_summary.status_code == 200
    data_summary = res_summary.json()
    assert data_summary["total_predictions"] == 0
    assert data_summary["average_aqi"] == 0.0

    # Test trends when empty
    res_trends = client.get("/api/analytics/trends")
    assert res_trends.status_code == 200
    assert res_trends.json()["points_count"] == 0


def test_prediction_storage_and_history_retrieval(client, sample_prediction_payload):
    # 1. Execute prediction via POST /api/predict
    res_predict = client.post("/api/predict", json=sample_prediction_payload)
    assert res_predict.status_code == 200
    pred_aqi = res_predict.json()["prediction"]["aqi"]

    # 2. Check that it was saved into prediction history
    res_hist = client.get("/api/predictions/history")
    assert res_hist.status_code == 200
    data_hist = res_hist.json()
    assert data_hist["count"] == 1
    assert data_hist["total"] == 1
    item = data_hist["history"][0]
    assert item["predicted_aqi"] == pred_aqi
    assert item["pm25"] == 45.2
    assert item["temperature"] == 27.5

    # 3. Check latest endpoint
    res_latest = client.get("/api/predictions/latest")
    assert res_latest.status_code == 200
    data_latest = res_latest.json()
    assert data_latest["predicted_aqi"] == pred_aqi
    assert data_latest["city"] is not None


def test_analytics_summary_and_trends_calculation(client, sample_prediction_payload):
    # Create multiple predictions
    client.post("/api/predict", json=sample_prediction_payload)

    payload2 = sample_prediction_payload.copy()
    payload2["pm25"] = 80.0
    client.post("/api/predict", json=payload2)

    # Test summary calculations
    res_summary = client.get("/api/analytics/summary?hours=24")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_predictions"] == 2
    assert summary["average_aqi"] > 0.0
    assert summary["max_aqi"] >= summary["min_aqi"]
    assert summary["current_aqi"] is not None

    # Test trends
    res_trends = client.get("/api/analytics/trends?hours=24")
    assert res_trends.status_code == 200
    trends = res_trends.json()
    assert trends["points_count"] == 2
    assert len(trends["trends"]) == 2
    assert trends["trends"][0]["aqi"] > 0


def test_pagination_and_query_limits(client, sample_prediction_payload):
    # Insert 5 predictions
    for _ in range(5):
        client.post("/api/predict", json=sample_prediction_payload)

    res_page1 = client.get("/api/predictions/history?limit=2&offset=0")
    assert res_page1.status_code == 200
    assert res_page1.json()["count"] == 2
    assert res_page1.json()["total"] == 5

    res_page2 = client.get("/api/predictions/history?limit=2&offset=2")
    assert res_page2.status_code == 200
    assert res_page2.json()["count"] == 2


def test_invalid_query_parameters(client):
    # Negative limit
    res = client.get("/api/predictions/history?limit=-5")
    assert res.status_code == 422

    # Exceeding max limit (>100)
    res = client.get("/api/predictions/history?limit=500")
    assert res.status_code == 422
