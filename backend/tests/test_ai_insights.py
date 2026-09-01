import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.utils.aqi import get_aqi_category_and_risk
from app.services.ai_insights_service import AIInsightsService

# In-memory test SQLite setup
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


def test_aqi_category_and_risk_utility():
    # 1. Good
    cat, risk, color, summary = get_aqi_category_and_risk(35.0)
    assert cat == "Good"
    assert risk == "Low Risk"
    assert color == "#10B981"

    # 2. Moderate
    cat, risk, color, summary = get_aqi_category_and_risk(75.0)
    assert cat == "Moderate"
    assert risk == "Moderate Risk"

    # 3. Unhealthy for sensitive groups
    cat, risk, color, summary = get_aqi_category_and_risk(125.0)
    assert cat == "Unhealthy for Sensitive Groups"
    assert risk == "Elevated Risk"

    # 4. Unhealthy
    cat, risk, color, summary = get_aqi_category_and_risk(180.0)
    assert cat == "Unhealthy"
    assert risk == "High Risk"

    # 5. Very Unhealthy
    cat, risk, color, summary = get_aqi_category_and_risk(250.0)
    assert cat == "Very Unhealthy"

    # 6. Hazardous
    cat, risk, color, summary = get_aqi_category_and_risk(350.0)
    assert cat == "Hazardous"
    assert risk == "Hazardous Risk"


def test_dominant_pollutant_extraction():
    pollutants = {
        "pm25": 85.0,  # 85 / 60 = 1.41
        "pm10": 90.0,  # 90 / 100 = 0.9
        "co": 0.5,     # 0.5 / 2.0 = 0.25
        "no2": 20.0,
        "so2": 5.0,
        "o3": 30.0,
    }
    top = AIInsightsService.extract_top_pollutants(pollutants)
    assert top[0] == "PM2.5"
    assert "PM10" in top


def test_get_insights_endpoint(client):
    # Test GET /api/insights
    res = client.get("/api/insights")
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert "aqi" in data
    assert "category" in data
    assert "risk_level" in data
    assert "trend" in data
    assert isinstance(data["primary_pollutants"], list)
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0
    assert "outdoor_activity" in data
    assert "ventilation" in data
    assert "mask_recommendation" in data
    assert data["generated_by"] == "rule_based"


def test_post_insights_custom_input(client):
    # Test POST /api/insights
    payload = {
        "aqi": 165.0,
        "pm25": 95.0,
        "pm10": 160.0,
        "temperature": 28.0,
        "humidity": 65.0,
    }
    res = client.post("/api/insights", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert data["aqi"] == 165.0
    assert data["category"] == "Unhealthy"
    assert data["risk_level"] == "High Risk"
    assert "PM2.5" in data["primary_pollutants"]
    assert "N95" in data["mask_recommendation"]


def test_insights_without_external_api_key(client):
    # Ensures insights function 100% reliably in deterministic offline mode
    payload = {"pm25": 30.0, "pm10": 50.0}
    res = client.post("/api/insights", json=payload)
    assert res.status_code == 200
    assert res.json()["generated_by"] == "rule_based"


def test_invalid_input_validation(client):
    res = client.post("/api/insights", json={"aqi": -50.0})
    assert res.status_code == 422
