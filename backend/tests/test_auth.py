import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.models import User, Prediction, Location
from app.utils.security import get_password_hash, create_access_token

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


def test_user_registration_success(client):
    payload = {
        "name": "Alice Tester",
        "email": "alice@example.com",
        "password": "Password123",
        "confirm_password": "Password123",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["name"] == "Alice Tester"
    assert "hashed_password" not in data["user"]


def test_user_registration_duplicate_email(client):
    payload = {
        "name": "Alice Tester",
        "email": "alice@example.com",
        "password": "Password123",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409


def test_user_registration_weak_password(client):
    payload = {
        "name": "Bob Tester",
        "email": "bob@example.com",
        "password": "weak",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 422


def test_user_registration_password_mismatch(client):
    payload = {
        "name": "Bob Tester",
        "email": "bob@example.com",
        "password": "Password123",
        "confirm_password": "DifferentPassword123",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 422


def test_user_login_success_and_failure(client):
    # Register
    client.post("/api/auth/register", json={
        "name": "Charlie",
        "email": "charlie@example.com",
        "password": "Password123",
    })

    # Correct Login
    res = client.post("/api/auth/login", json={
        "email": "charlie@example.com",
        "password": "Password123",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

    # Wrong Password
    res_wrong = client.post("/api/auth/login", json={
        "email": "charlie@example.com",
        "password": "WrongPassword123",
    })
    assert res_wrong.status_code == 401


def test_get_current_user_profile_and_update(client):
    reg = client.post("/api/auth/register", json={
        "name": "David",
        "email": "david@example.com",
        "password": "Password123",
    }).json()
    token = reg["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # GET /api/auth/me
    res_me = client.get("/api/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "david@example.com"

    # PUT /api/users/me
    res_update = client.put("/api/users/me", headers=headers, json={"name": "David Updated"})
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "David Updated"


def test_change_password(client):
    reg = client.post("/api/auth/register", json={
        "name": "Eve",
        "email": "eve@example.com",
        "password": "Password123",
    }).json()
    token = reg["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Change password
    res_change = client.post("/api/users/change-password", headers=headers, json={
        "current_password": "Password123",
        "new_password": "NewSecurePassword456",
        "confirm_new_password": "NewSecurePassword456",
    })
    assert res_change.status_code == 200

    # Login with new password
    res_login = client.post("/api/auth/login", json={
        "email": "eve@example.com",
        "password": "NewSecurePassword456",
    })
    assert res_login.status_code == 200


def test_user_prediction_isolation(client):
    # Register User A
    user_a = client.post("/api/auth/register", json={
        "name": "User A",
        "email": "usera@example.com",
        "password": "Password123",
    }).json()
    token_a = user_a["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    user_b = client.post("/api/auth/register", json={
        "name": "User B",
        "email": "userb@example.com",
        "password": "Password123",
    }).json()
    token_b = user_b["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

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

    # User A creates prediction
    client.post("/api/predict", json=pred_payload, headers=headers_a)

    # Check User A history (should have 1)
    res_hist_a = client.get("/api/predictions/history", headers=headers_a)
    assert res_hist_a.status_code == 200
    assert res_hist_a.json()["count"] == 1

    # Check User B history (should have 0)
    res_hist_b = client.get("/api/predictions/history", headers=headers_b)
    assert res_hist_b.status_code == 200
    assert res_hist_b.json()["count"] == 0
