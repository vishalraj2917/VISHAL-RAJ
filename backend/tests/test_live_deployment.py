import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings, Settings
from app.main import app
from app.database import Base, get_db
from app.services.prediction_service import PredictionService

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


def test_cors_origin_parser():
    # Test comma-separated string parsing in Settings
    custom_settings = Settings(CORS_ORIGINS="https://app.vercel.app,https://admin.vercel.app")
    assert "https://app.vercel.app" in custom_settings.CORS_ORIGINS
    assert "https://admin.vercel.app" in custom_settings.CORS_ORIGINS


def test_required_ml_model_artifacts_exist():
    service = PredictionService.get_instance()
    assert service.model_path.exists()
    assert service.preprocessor_path.exists()
    assert service.is_ready()


def test_cloud_readiness_probe(client):
    res = client.get("/api/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"
    assert data["ml_model"] == "ok"


def test_cloud_health_liveness_probe(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["ml_model"] == "ready"


def test_environment_configuration_defaults():
    assert settings.DATABASE_URL is not None
    assert settings.SECRET_KEY is not None
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES >= 15
