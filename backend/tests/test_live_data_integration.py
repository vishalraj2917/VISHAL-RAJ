import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.weather_service import WeatherService
from app.services.air_quality_service import AirQualityService
from app.services.live_feature_service import LiveFeatureService
from app.services.cache_service import live_data_cache


@pytest.fixture(autouse=True)
def clear_cache():
    live_data_cache.clear()
    yield
    live_data_cache.clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_weather_data():
    return {
        "temperature": 28.5,
        "humidity": 65.0,
        "wind_speed": 4.2,
        "pressure": 1011.0,
        "timestamp": "2026-09-01T14:00",
        "timezone": "Asia/Kolkata",
    }


@pytest.fixture
def mock_air_quality_data():
    return {
        "pm25": 42.0,
        "pm10": 80.0,
        "co": 0.75,
        "no2": 22.0,
        "so2": 10.5,
        "o3": 26.0,
        "timestamp": "2026-09-01T14:00",
        "timezone": "Asia/Kolkata",
    }


def test_live_feature_service_builds_21_features(mock_weather_data, mock_air_quality_data):
    req, raw = LiveFeatureService.build_features(mock_air_quality_data, mock_weather_data)

    # 1. Primary Pollutants
    assert req.pm25 == 42.0
    assert req.pm10 == 80.0
    assert req.co == 0.75
    assert req.no2 == 22.0
    assert req.so2 == 10.5
    assert req.o3 == 26.0

    # 2. Weather
    assert req.temperature == 28.5
    assert req.humidity == 65.0
    assert req.wind_speed == 4.2
    assert req.pressure == 1011.0

    # 3. Time
    assert req.hour == 14
    assert req.day == 1
    assert req.month == 9
    assert req.day_of_week == 1  # Tuesday

    # 4. Derived & Interactions (Exact formulas)
    expected_pm_ratio = round(42.0 / (80.0 + 1e-5), 4)
    assert abs(raw["pm_ratio"] - expected_pm_ratio) < 1e-3

    expected_thi = (28.5 * 65.0) / 100.0
    assert abs(raw["temp_humidity_idx"] - expected_thi) < 1e-3


def test_predict_live_success(client, mock_weather_data, mock_air_quality_data):
    with patch.object(WeatherService, "fetch_current_weather", new_callable=AsyncMock) as mock_weather, \
         patch.object(AirQualityService, "fetch_current_air_quality", new_callable=AsyncMock) as mock_aq:

        mock_weather.return_value = mock_weather_data
        mock_aq.return_value = mock_air_quality_data

        payload = {
            "latitude": 12.9716,
            "longitude": 77.5946
        }
        response = client.post("/api/predict/live", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["location"]["latitude"] == 12.9716
        assert data["location"]["longitude"] == 77.5946
        assert data["air_quality"]["pm25"] == 42.0
        assert data["weather"]["temperature"] == 28.5
        assert "prediction" in data
        assert isinstance(data["prediction"]["aqi"], (int, float))
        assert data["prediction"]["aqi"] > 0.0
        assert data["prediction"]["category"] in ["Good", "Moderate", "Unhealthy for Sensitive Groups", "Poor / Unhealthy"]
        assert data["model"]["name"] == "Gradient Boosting"


def test_predict_live_invalid_coordinates(client):
    # Invalid latitude > 90
    response = client.post("/api/predict/live", json={"latitude": 105.0, "longitude": 77.5946})
    assert response.status_code == 422

    # Invalid longitude < -180
    response = client.post("/api/predict/live", json={"latitude": 12.9716, "longitude": -195.0})
    assert response.status_code == 422


def test_predict_live_api_timeout_handling(client):
    with patch.object(WeatherService, "fetch_current_weather", new_callable=AsyncMock) as mock_weather:
        mock_weather.side_effect = TimeoutError("Weather provider timed out")

        payload = {"latitude": 12.9716, "longitude": 77.5946}
        response = client.post("/api/predict/live", json=payload)
        assert response.status_code == 502
        data = response.json()
        assert "LIVE_DATA_UNAVAILABLE" in data["detail"]


def test_predict_live_api_connection_error_handling(client):
    with patch.object(AirQualityService, "fetch_current_air_quality", new_callable=AsyncMock) as mock_aq:
        mock_aq.side_effect = ConnectionError("Air quality provider unavailable")

        payload = {"latitude": 12.9716, "longitude": 77.5946}
        response = client.post("/api/predict/live", json=payload)
        assert response.status_code == 502
        data = response.json()
        assert "LIVE_DATA_UNAVAILABLE" in data["detail"]


def test_predict_live_missing_pollutant_handling(client):
    with patch.object(AirQualityService, "fetch_current_air_quality", new_callable=AsyncMock) as mock_aq:
        mock_aq.side_effect = ValueError("Missing critical pollutant metrics")

        payload = {"latitude": 12.9716, "longitude": 77.5946}
        response = client.post("/api/predict/live", json=payload)
        assert response.status_code == 502
        data = response.json()
        assert "LIVE_DATA_UNAVAILABLE" in data["detail"]


def test_caching_behavior(mock_weather_data, mock_air_quality_data):
    live_data_cache.set(12.9716, 77.5946, "weather", mock_weather_data)
    cached = live_data_cache.get(12.9716, 77.5946, "weather")
    assert cached == mock_weather_data

    # Different coordinates should miss cache
    assert live_data_cache.get(28.7041, 77.1025, "weather") is None
