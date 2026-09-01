# Phase 9: AI Features Documentation

## 1. Overview
Phase 9 introduces three intelligent, context-aware AI capabilities on top of the verified `GradientBoostingRegressor` numerical ML model:
1. **AI Air Quality Chatbot (`POST /api/ai/chat`)**: Real-time conversational assistant explaining atmospheric science, pollutant dynamics, and safety recommendations.
2. **AI Air Quality Report Generator (`POST /api/ai/report`)**: Executive summary and analytical synthesis of telemetry, dispersion meteorology, and public health action items.
3. **Personalized Health & Safety Advisor (`POST /api/ai/health-advice`)**: Tailored activity and target group recommendations (e.g. running, cycling, commuting, sensitive groups) with exposure-reduction guidance.

---

## 2. Core Architectural Principles & Boundaries

- **Authoritative Numerical Predictions**: The ML model (`models/best_model.joblib`) strictly remains the single source of truth for the continuous numerical AQI value ($R^2 = 0.99$). The AI layer provides interpretation, explanation, and recommendations without fabricating or altering data.
- **Medical Safety Boundaries**: The system explicitly enforces that all AI outputs are for general awareness and exposure reduction only. Prompts and schemas strictly prevent medical diagnosis, prescriptions, or treatment plans.
- **AI Abstraction & Resilient Fallback**: The backend `AIService` connects to Google Gemini API when `AI_API_KEY` is configured and seamlessly falls back to a deterministic rule-based environmental knowledge engine if the network is offline or no key is set.

---

## 3. API Endpoints

### 1. AI Chatbot
- **Endpoint**: `POST /api/ai/chat`
- **Request Body**:
```json
{
  "message": "Is it safe to go for a run right now?",
  "context": {
    "latitude": 12.9716,
    "longitude": 77.5946,
    "predicted_aqi": 68.5,
    "aqi_category": "Moderate",
    "dominant_pollutant": "PM2.5",
    "pm25": 28.4,
    "pm10": 55.2,
    "temperature": 27.5,
    "humidity": 60.0
  },
  "history": []
}
```
- **Response Body (`HTTP 200 OK`)**:
```json
{
  "success": true,
  "reply": "The current predicted AQI is 68.5 (Moderate). Air quality is acceptable for most people; however, unusually sensitive individuals should consider reducing prolonged heavy outdoor exertion.",
  "context_used": true,
  "disclaimer": "This information is for general awareness and does not replace medical advice from a qualified healthcare professional.",
  "timestamp": "2026-09-01T14:30:00Z"
}
```

### 2. AI Executive Report
- **Endpoint**: `POST /api/ai/report`
- **Request Body**: Accepts `context` object with live environmental telemetry.
- **Response Body (`HTTP 200 OK`)**: Returns structured sections: `summary`, `air_quality_analysis`, `weather_impact`, and `safety_recommendations`.

### 3. Personalized Health Advisor
- **Endpoint**: `POST /api/ai/health-advice`
- **Request Body**: Accepts `activity` (e.g. "Outdoor Exercise"), `target_group` (e.g. "Sensitive Groups"), and environmental `context`.
- **Response Body (`HTTP 200 OK`)**: Returns `safety_rating` ("Safe", "Caution", "Unfavorable"), `advice`, and `recommended_precautions`.

---

## 4. Frontend Components

- `frontend/src/components/AIChatbot.jsx`: Glassmorphic chat interface with quick-prompt chips and conversation memory.
- `frontend/src/components/AIReportGenerator.jsx`: Executive summary report card with structured section badges.
- `frontend/src/components/AIHealthAdvisor.jsx`: Activity and audience selection form with safety badges and actionable precautions.

---

## 5. Automated Verification & Testing

- **Backend Test Suite**: `36/36 PASSED` (Phase 4: 5, Phase 5: 4, Phase 6: 13, Phase 7: 7, Phase 9: 7).
- **Frontend Production Build**: `npm run build` completed with 0 errors.
