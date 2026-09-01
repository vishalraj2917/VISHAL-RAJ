# Phase 9: AI Insights & Smart Recommendations Documentation

## 1. Overview
Phase 9 introduces a dedicated, high-reliability AI Insights & Smart Recommendations service on top of the GradientBoostingRegressor model. It provides clear explainability, dominant pollutant ranking, historical trend analysis, and safety-focused action plans without replacing the ML model or requiring mandatory third-party AI keys.

---

## 2. Architectural Highlights

- **Centralized AQI Category Engine**: `backend/app/utils/aqi.py` maps continuous numerical AQI to standardized risk levels and colors (Good, Moderate, Unhealthy for Sensitive Groups, Unhealthy, Very Unhealthy, Hazardous).
- **Dominant Pollutant Analysis**: Evaluates normalized ratios across PM2.5, PM10, CO, NO2, SO2, and O3 to identify primary and secondary contributors.
- **Deterministic Offline Fallback**: 100% reliable rule-based inference engine that operates without external network dependencies or API keys.

---

## 3. API Endpoints

### 1. Current System Insights
- **Endpoint**: `GET /api/insights`
- **Response**:
```json
{
  "success": true,
  "aqi": 68.9,
  "category": "Moderate",
  "risk_level": "Moderate Risk",
  "color": "#F59E0B",
  "trend": "Stable",
  "primary_pollutants": ["PM2.5", "PM10"],
  "summary": "Air quality is currently classified as Moderate (Moderate Risk) with a predicted AQI of 68.9 in Bengaluru. Primary atmospheric pollution is driven by elevated PM2.5. Historical trend direction is evaluated as Stable.",
  "recommendations": [
    "Sensitive individuals should monitor for mild throat or eye irritation.",
    "Consider checking local AQI before extended high-intensity workouts.",
    "Keep windows closed during peak vehicular commute hours."
  ],
  "outdoor_activity": "Suitable for most people. Sensitive groups should take frequent breaks during vigorous exertion.",
  "ventilation": "Natural ventilation is acceptable; use air purifiers if residing near main roads.",
  "mask_recommendation": "Optional; recommended only for unusually sensitive individuals.",
  "confidence": 0.95,
  "generated_by": "rule_based",
  "last_updated": "2026-09-01T14:55:00Z"
}
```

### 2. Custom Input Insights
- **Endpoint**: `POST /api/insights`
- **Request Body**: Accepts custom `aqi`, `pm25`, `pm10`, `co`, `no2`, `so2`, `o3`, `temperature`, and `humidity` values.

---

## 4. Frontend Component

- **`AIInsightsPanel.jsx`**: Glassmorphic panel displaying:
  - Top Metric Cards (Predicted AQI, Evaluated Risk, Trend, and Primary Pollutants)
  - Executive AI Diagnosis & Outdoor Activity Guidance
  - Ventilation Advice & Protective Mask Guidelines
  - Actionable Health & Lifestyle Action Items
  - Manual "Refresh Insights" trigger

---

## 5. Verification Results

- **Backend Pytest Suite**: **53/53 tests PASSED**
- **Frontend Production Build**: `npm run build` executed in 5.49s with **0 errors**.
