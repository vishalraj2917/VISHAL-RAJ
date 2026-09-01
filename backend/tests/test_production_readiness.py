import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.config import settings

# Create in-memory SQLite for testing readiness and health probes
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


def test_production_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["ml_model"] == "ready"


def test_production_readiness_endpoint(client):
    res = client.get("/api/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"
    assert data["ml_model"] == "ok"


def test_root_endpoint_metadata(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "version" in data
    assert "environment" in data


def test_request_timing_headers(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "x-process-time-ms" in res.headers


def test_cors_headers(client):
    res = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_safe_error_masking(client):
    # Pass malformed JSON payload
    res = client.post("/api/predict", content="not-a-json", headers={"Content-Type": "application/json"})
    assert res.status_code in [422, 400, 500]
    # Verify no raw python file path leaks
    body_text = res.text
    assert "Traceback" not in body_text
