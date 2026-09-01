# Phase 6: ML Prediction API Integration Documentation

## 1. Overview
Phase 6 connects the trained champion Machine Learning model (`Gradient Boosting Regressor`) with the FastAPI backend REST API. It provides high-performance, validated, and resilient inference endpoints for real-time Air Quality Index (AQI) forecasting and health category classification.

---

## 2. API Endpoints Summary

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/predict` | Single-sample AQI prediction with full category & advisory classification | None |
| `POST` | `/api/predict/batch` | Vectorized batch predictions (up to 100 records) | None |
| `GET` | `/api/model/info` | Retrieves active ML model metadata, architecture, and benchmark metrics | None |
| `GET` | `/api/health` | Backend & ML model readiness health check | None |
| `GET` | `/docs` | Interactive Swagger UI API documentation | None |

---

## 3. Machine Learning Model & Artifacts

- **Champion Model**: Gradient Boosting Regressor (`sklearn.ensemble.GradientBoostingRegressor`)
- **Artifact Path**: `models/best_model.joblib`
- **Preprocessor Pipeline**: `models/preprocessor.joblib` (RobustScaler + Imputer fitted on Phase 4 training set)
- **Metadata**: `models/model_metadata.json`
- **Target Variable**: `aqi` (Continuous numerical target)
- **Validation RMSE**: `1.1772` | **Test RMSE**: `1.3798` | **Test $R^2$**: `0.9914`

---

## 4. Input Features & Validation Rules

The API expects 21 model features. Primary environmental features are strictly validated for physical feasibility and type correctness:

### Primary Pollutants:
- `pm25` (float, $\ge 0.0, \le 1000.0$ $\mu\text{g/m}^3$)
- `pm10` (float, $\ge 0.0, \le 1500.0$ $\mu\text{g/m}^3$)
- `co` (float, $\ge 0.0, \le 100.0$ $\text{mg/m}^3$)
- `no2` (float, $\ge 0.0, \le 1000.0$ $\mu\text{g/m}^3$)
- `so2` (float, $\ge 0.0, \le 1000.0$ $\mu\text{g/m}^3$)
- `o3` (float, $\ge 0.0, \le 1000.0$ $\mu\text{g/m}^3$)

### Weather Parameters:
- `temperature` (float, $\ge -50.0, \le 60.0$ $^\circ\text{C}$)
- `humidity` (float, $\ge 0.0, \le 100.0$ $\%$)
- `wind_speed` (float, $\ge 0.0, \le 150.0$ $\text{km/h}$ / $\text{m/s}$)
- `pressure` (float, $\ge 800.0, \le 1100.0$ $\text{hPa}$)

### Temporal Parameters:
- `hour` (int, $0 \le \text{hour} \le 23$)
- `day` (int, $1 \le \text{day} \le 31$)
- `month` (int, $1 \le \text{month} \le 12$)
- `day_of_week` (int, $0 \le \text{day\_of\_week} \le 6$)
- `is_weekend` (int, $0$ or $1$)

### Derived Features (Auto-computed by server if omitted):
- `hour_sin`, `hour_cos` ($\sin/\cos$ cyclical encoding of `hour`)
- `month_sin`, `month_cos` ($\sin/\cos$ cyclical encoding of `month`)
- `pm_ratio` ($\frac{\text{PM2.5}}{\text{PM10}}$)
- `temp_humidity_idx` ($\frac{\text{temperature} \times \text{humidity}}{100}$)

---

## 5. AQI Classification & Color Mapping

The prediction service automatically maps the continuous predicted AQI to national standard air quality index categories:

| AQI Range | Category | Color Code | Health Advisory |
| :--- | :--- | :---: | :--- |
| **0 – 50** | Good | `#10B981` | Satisfactory; pollution poses little or no risk. |
| **51 – 100** | Moderate | `#FBBF24` | Acceptable; sensitive individuals should consider limiting prolonged outdoor exertion. |
| **101 – 200** | Unhealthy for Sensitive Groups | `#F97316` | Members of sensitive groups may experience health effects. |
| **201 – 300** | Poor / Unhealthy | `#EF4444` | Everyone may begin to experience adverse health effects. |
| **301 – 400** | Very Poor / Severe | `#8B5CF6` | Health alert: Significant risk of respiratory and cardiovascular irritation. |
| **401+** | Hazardous | `#7F1D1D` | Emergency conditions: Everyone should avoid all outdoor physical activity. |

---

## 6. Request & Response Examples

### Single Prediction Request (`POST /api/predict`)

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

### Successful Response (`HTTP 200 OK`)

```json
{
  "success": true,
  "prediction": {
    "aqi": 68.87,
    "category": "Moderate",
    "color": "#FBBF24",
    "dominant_pollutant": "PM2.5",
    "health_advisory": "Air quality is acceptable; however, some pollutants may be a concern for very sensitive people."
  },
  "model": {
    "name": "Gradient Boosting",
    "type": "GradientBoostingRegressor",
    "target": "aqi",
    "validation_rmse": 1.1772,
    "test_rmse": 1.3798
  },
  "timestamp": "2026-09-01T14:15:00.000000Z"
}
```

---

## 7. Error Handling

- **HTTP 422 Unprocessable Entity**: Triggered when fields are missing, of incorrect data types, contain `NaN` or `Infinity`, or fall outside physical feasibility limits.
- **HTTP 500 Internal Server Error**: Sanitized error returned if artifacts cannot be loaded or inference engine encounters a critical failure. Python stack traces are never exposed to clients.

---

## 8. How to Start FastAPI Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive documentation is available at:
`http://127.0.0.1:8000/docs`

---

## 9. Testing via cURL / PowerShell

```powershell
curl -X POST "http://127.0.0.1:8000/api/predict" `
  -H "Content-Type: application/json" `
  -d '{
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
  }'
```

---

## 10. Automated Tests

Run the full backend test suite:
```powershell
$env:PYTHONPATH=".;backend"
backend\.venv\Scripts\pytest.exe backend/tests -v
```
All 22/22 unit and integration tests passing.
