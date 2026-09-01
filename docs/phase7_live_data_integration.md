# Phase 7: Live Weather & Air Quality Data Integration Documentation

## 1. Overview
Phase 7 integrates live meteorological and atmospheric pollutant APIs into the FastAPI backend. Users can specify geographic coordinates (`latitude`, `longitude`), and the system will automatically:
1. Concurrently fetch real-time atmospheric readings (PM2.5, PM10, CO, NO2, SO2, O3) and meteorological conditions (temperature, humidity, wind speed, pressure).
2. Normalize metrics and units into exact ML project standards.
3. Automatically perform feature engineering (temporal cyclical encodings, pollutant ratio, heat index) yielding exactly the 21 ML features.
4. Execute real-time inference via the champion `GradientBoostingRegressor` model.
5. Return formatted AQI predictions, qualitative categories, color coding, and health advisories.

---

## 2. Live Data Provider & Architecture

- **Provider**: [Open-Meteo](https://open-meteo.com) Weather & Air Quality API (Open-access WMO-compliant global meteorological and atmospheric models).
- **Weather API URL**: `https://api.open-meteo.com/v1/forecast`
- **Air Quality API URL**: `https://air-quality-api.open-meteo.com/v1/air-quality`
- **Authentication**: Optional API key configurable via `AIR_QUALITY_API_KEY` / `WEATHER_API_KEY` in `backend/.env`. Public rate tier active by default.
- **Caching**: Thread-safe in-memory spatial TTL cache (`300s` / 5 minutes) configured at $\sim 110\text{m}$ resolution to prevent redundant third-party API queries.
- **Resilience**: Request timeout of 10.0 seconds with error handling returning `502 Bad Gateway` (`LIVE_DATA_UNAVAILABLE`) if external providers are unreachable.

---

## 3. Data Ingestion & Unit Normalization

| Environmental Metric | Raw API Parameter | Normalized Unit | Model Requirement |
| :--- | :--- | :---: | :---: |
| **PM2.5** | `pm2_5` | $\mu\text{g/m}^3$ | $\mu\text{g/m}^3$ |
| **PM10** | `pm10` | $\mu\text{g/m}^3$ | $\mu\text{g/m}^3$ |
| **CO** | `carbon_monoxide` | $\text{mg/m}^3$ | $\text{mg/m}^3$ (converted from $\mu\text{g/m}^3$ $\div 1000$) |
| **NO2** | `nitrogen_dioxide` | $\mu\text{g/m}^3$ | $\mu\text{g/m}^3$ |
| **SO2** | `sulphur_dioxide` | $\mu\text{g/m}^3$ | $\mu\text{g/m}^3$ |
| **O3** | `ozone` | $\mu\text{g/m}^3$ | $\mu\text{g/m}^3$ |
| **Temperature** | `temperature_2m` | $^\circ\text{C}$ | $^\circ\text{C}$ |
| **Humidity** | `relative_humidity_2m` | $\%$ | $\%$ |
| **Wind Speed** | `wind_speed_10m` | $\text{km/h}$ | $\text{km/h}$ |
| **Pressure** | `surface_pressure` | $\text{hPa}$ | $\text{hPa}$ |

---

## 4. Live Feature Engineering (21 Features)

The `LiveFeatureService` processes the normalized data and observation timestamps using the exact Phase 4 mathematical formulations:

1. **Temporal Features**: `hour`, `day`, `month`, `day_of_week`, `is_weekend` parsed with timezone awareness.
2. **Cyclical Encodings**:
   $$\text{hour\_sin} = \sin\left(\frac{2\pi \cdot \text{hour}}{24}\right), \quad \text{hour\_cos} = \cos\left(\frac{2\pi \cdot \text{hour}}{24}\right)$$
   $$\text{month\_sin} = \sin\left(\frac{2\pi \cdot (\text{month} - 1)}{12}\right), \quad \text{month\_cos} = \cos\left(\frac{2\pi \cdot (\text{month} - 1)}{12}\right)$$
3. **Domain Interactions**:
   $$\text{pm\_ratio} = \text{clip}\left(\frac{\text{PM2.5}}{\text{PM10} + 10^{-5}}, 0.0, 1.5\right)$$
   $$\text{temp\_humidity\_idx} = \frac{\text{temperature} \times \text{humidity}}{100}$$

---

## 5. API Endpoints

### `POST /api/predict/live`
Accepts latitude and longitude and returns full environmental observations and predicted AQI.

#### Request Body
```json
{
  "latitude": 12.9716,
  "longitude": 77.5946
}
```

#### Response Body (`HTTP 200 OK`)
```json
{
  "success": true,
  "location": {
    "latitude": 12.9716,
    "longitude": 77.5946,
    "city_name": null
  },
  "air_quality": {
    "pm25": 4.6,
    "pm10": 6.9,
    "co": 0.191,
    "no2": 1.6,
    "so2": 2.3,
    "o3": 74.0
  },
  "weather": {
    "temperature": 28.7,
    "humidity": 55.0,
    "wind_speed": 12.8,
    "pressure": 911.8
  },
  "prediction": {
    "aqi": 7.8,
    "category": "Good",
    "color": "#10B981",
    "dominant_pollutant": "O3",
    "health_advisory": "Air quality is considered satisfactory, and air pollution poses little or no risk."
  },
  "model": {
    "name": "Gradient Boosting",
    "type": "GradientBoostingRegressor",
    "target": "aqi",
    "validation_rmse": 1.1772,
    "test_rmse": 1.3798
  },
  "observed_at": "2026-09-01T14:15",
  "timestamp": "2026-09-01T08:52:17.488022Z"
}
```

---

## 6. Error Handling & Fallback Behavior

- **HTTP 422 Unprocessable Entity**: Returned when coordinates are invalid (e.g. $|\text{lat}| > 90$ or $|\text{lon}| > 180$) or non-numeric/NaN.
- **HTTP 502 Bad Gateway**: Returned when external meteorological or air quality providers timeout, fail, or return missing variables. **No fake or invented fallback data is generated.**
- **HTTP 500 Internal Server Error**: Returned if internal ML inference fails.

---

## 7. Automated Test Suite

Run the full regression test suite across all project phases:
```powershell
$env:PYTHONPATH=".;backend"
backend\.venv\Scripts\pytest.exe backend/tests -v
```

### Test Coverage Summary:
- **Phase 4 Pipeline Tests**: 5/5 PASSED
- **Phase 5 ML Model Tests**: 4/4 PASSED
- **Phase 6 Prediction API Tests**: 13/13 PASSED
- **Phase 7 Live Integration Tests**: 7/7 PASSED
- **Total Suite**: **29/29 PASSED**
