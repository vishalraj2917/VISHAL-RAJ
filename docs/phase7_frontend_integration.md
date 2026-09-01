# Phase 7: Full Frontend Integration & End-to-End System Documentation

## 1. Overview
Phase 7 integrates the complete React (Vite) frontend with the FastAPI backend and trained `GradientBoostingRegressor` machine learning model. It provides real-time environmental forecasting, manual parameter simulation, telemetry visualization, system health status, and multi-container Docker deployment support.

---

## 2. System Architecture

```text
                  USER (Browser)
                        │
                        ▼
               React SPA (Port 3000)
              (Vite + Axios + Recharts)
                        │
       ┌────────────────┴────────────────┐
       ▼                                 ▼
POST /api/predict/live            POST /api/predict
(Live Coordinates)             (Custom 21 Parameters)
       │                                 │
       └────────────────┬────────────────┘
                        ▼
               FastAPI Backend (Port 8000)
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
     Feature Engineering     ML Preprocessor
     (Temporal + Domain)  (models/preprocessor.joblib)
             │                     │
             └──────────┬──────────┘
                        ▼
          Gradient Boosting Model Inference
             (models/best_model.joblib)
                        │
                        ▼
               Predicted AQI & Category
                        │
                        ▼
               React Dashboard UI
```

---

## 3. Frontend Components & Responsibilities

- **`DashboardHeader.jsx`**: Displays system branding, live API health indicator (`GET /api/health`), and manual refresh triggers.
- **`LocationSelector.jsx`**: Coordinates input (`latitude`, `longitude`), browser GPS detection (`navigator.geolocation`), and quick-select presets.
- **`AQICard.jsx`**: Circular AQI gauge meter, qualitative status badge, dominant pollutant identification, and health advisory.
- **`PollutantGrid.jsx`**: Normalized real-time telemetry cards for PM2.5, PM10, CO, NO2, SO2, and O3.
- **`WeatherGrid.jsx`**: Meteorological metrics for Temperature, Humidity, Wind Speed, and Atmospheric Pressure.
- **`DashboardCharts.jsx`**: Recharts bar chart for pollutant concentrations and half-dial radial gauge for AQI severity.
- **`ManualPredictionForm.jsx`**: Interactive 21-feature parameter simulation form communicating directly with `POST /api/predict`.
- **`AIChatbot.jsx`, `AIReportGenerator.jsx`, `AIHealthAdvisor.jsx`**: Context-aware AI features with medical boundary enforcement.
- **`StatusStates.jsx`**: Glassmorphic loading, error, and empty state fallbacks.

---

## 4. API Endpoints & Contracts

### 1. Health Endpoint
- **URL**: `GET http://127.0.0.1:8000/api/health`
- **Response**:
```json
{
  "status": "ok",
  "database": "connected",
  "ml_model": "ready",
  "model_name": "Gradient Boosting"
}
```

### 2. Live Prediction Endpoint
- **URL**: `POST http://127.0.0.1:8000/api/predict/live`
- **Payload**:
```json
{
  "latitude": 12.9716,
  "longitude": 77.5946
}
```

### 3. Manual Parameter Prediction Endpoint
- **URL**: `POST http://127.0.0.1:8000/api/predict`
- **Payload**:
```json
{
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
```

---

## 5. Docker & Container Deployment

- **Backend Dockerfile**: `backend/Dockerfile` (Python 3.11-slim, multi-stage dependency install, Uvicorn on port 8000).
- **Frontend Dockerfile**: `frontend/Dockerfile` (Node.js 20-alpine build stage, Nginx alpine distribution on port 3000).
- **Docker Compose**: `docker-compose.yml` orchestrates PostgreSQL 16, FastAPI backend, and React frontend.

---

## 6. Execution & Testing Commands

### Start Backend
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Start Frontend
```powershell
cd frontend
npm install
npm run dev
```

### Run Regression Test Suite
```powershell
$env:PYTHONPATH=".;backend"
backend\.venv\Scripts\pytest.exe backend/tests -v
```
All **36/36 tests passing** across all phases.
