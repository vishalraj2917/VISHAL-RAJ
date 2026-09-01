import pytest
import math
from fastapi.testclient import TestClient

from app.main import app
from app.services.prediction_service import PredictionService
from app.schemas.prediction import PredictionRequest
from ml.predict import predict_aqi as ml_predict_aqi


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_payload():
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


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code in [200, 503]
    data = response.json()
    if response.status_code == 200:
        assert data["status"] == "ok"
        assert data["ml_model"] == "ready"
        assert "database" in data


def test_prediction_service_direct():
    service = PredictionService.get_instance()
    assert service.is_ready()
    assert service.model is not None
    assert service.preprocessor is not None

    req = PredictionRequest(
        pm25=45.2,
        pm10=85.0,
        co=0.8,
        no2=24.5,
        so2=11.2,
        o3=28.0,
        temperature=27.5,
        humidity=62.0,
        wind_speed=3.8,
        pressure=1012.5,
        hour=14,
        day=15,
        month=6,
        day_of_week=2,
        is_weekend=0
    )
    res = service.predict_single(req)
    assert res.success is True
    assert isinstance(res.prediction.aqi, float)
    assert res.prediction.aqi >= 0.0
    assert res.prediction.category in [
        "Good", "Moderate", "Unhealthy for Sensitive Groups",
        "Poor / Unhealthy", "Very Poor / Severe", "Hazardous"
    ]


def test_predict_api_valid_input(client, valid_payload):
    response = client.post("/api/predict", json=valid_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "prediction" in data
    assert "aqi" in data["prediction"]
    assert "category" in data["prediction"]
    assert "color" in data["prediction"]
    assert "model" in data
    assert data["model"]["name"] == "Gradient Boosting"
    assert data["model"]["target"] == "aqi"
    assert isinstance(data["prediction"]["aqi"], (int, float))


def test_predict_api_model_consistency(client, valid_payload):
    direct_pred = ml_predict_aqi(valid_payload)
    response = client.post("/api/predict", json=valid_payload)
    assert response.status_code == 200
    api_pred = response.json()["prediction"]["aqi"]

    assert abs(api_pred - direct_pred) < 1e-2


def test_predict_api_missing_field(client, valid_payload):
    incomplete_payload = valid_payload.copy()
    del incomplete_payload["pm25"]

    response = client.post("/api/predict", json=incomplete_payload)
    assert response.status_code == 422


def test_predict_api_invalid_data_type(client, valid_payload):
    invalid_payload = valid_payload.copy()
    invalid_payload["pm25"] = "invalid_string_not_a_number"

    response = client.post("/api/predict", json=invalid_payload)
    assert response.status_code == 422


def test_predict_api_nan_value(client, valid_payload):
    nan_payload = valid_payload.copy()
    nan_payload["pm25"] = "nan"

    response = client.post("/api/predict", json=nan_payload)
    assert response.status_code == 422


def test_predict_api_inf_value(client, valid_payload):
    inf_payload = valid_payload.copy()
    inf_payload["temperature"] = "inf"

    response = client.post("/api/predict", json=inf_payload)
    assert response.status_code == 422


def test_predict_api_negative_values(client, valid_payload):
    invalid_payload = valid_payload.copy()
    invalid_payload["pm25"] = -10.0

    response = client.post("/api/predict", json=invalid_payload)
    assert response.status_code == 422


def test_predict_api_out_of_bounds(client, valid_payload):
    invalid_payload = valid_payload.copy()
    invalid_payload["temperature"] = 250.0

    response = client.post("/api/predict", json=invalid_payload)
    assert response.status_code == 422


def test_predict_api_hour_out_of_bounds(client, valid_payload):
    invalid_payload = valid_payload.copy()
    invalid_payload["hour"] = 25

    response = client.post("/api/predict", json=invalid_payload)
    assert response.status_code == 422


def test_batch_prediction_api(client, valid_payload):
    batch_payload = {
        "records": [valid_payload, valid_payload]
    }
    response = client.post("/api/predict/batch", json=batch_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["count"] == 2
    assert len(data["predictions"]) == 2
    assert data["predictions"][0]["aqi"] == data["predictions"][1]["aqi"]


def test_model_info_api(client):
    response = client.get("/api/model/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Gradient Boosting"
    assert data["type"] == "GradientBoostingRegressor"
    assert data["target"] == "aqi"
