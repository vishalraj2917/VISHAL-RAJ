# Phase 8: Frontend Dashboard & Visualizations Documentation

## 1. Overview
Phase 8 delivers a modern, responsive, glassmorphic Web Dashboard built with React, Vite, Axios, and Recharts. It connects to the FastAPI backend and provides real-time environmental visualizations, pollutant telemetry breakdown, meteorological status, and AI AQI forecasting with health advisories.

---

## 2. Dashboard Component Architecture

The frontend is structured into modular, reusable components located in `frontend/src/`:

```text
frontend/src/
├── components/
│   ├── DashboardHeader.jsx     # App branding, real-time health indicator, and refresh action
│   ├── LocationSelector.jsx    # Latitude/Longitude inputs, GPS locator, and preset city chips
│   ├── AQICard.jsx             # Circular AQI gauge meter, category badge, dominant pollutant, advisory
│   ├── PollutantGrid.jsx       # Individual telemetry cards for PM2.5, PM10, CO, NO2, SO2, O3
│   ├── WeatherGrid.jsx         # Individual metric cards for Temperature, Humidity, Wind, Pressure
│   ├── DashboardCharts.jsx     # Recharts BarChart for pollutants & RadialBarChart for AQI severity
│   └── StatusStates.jsx        # Glassmorphic Loading, Error, and Empty state indicators
├── services/
│   └── api.js                  # Axios client consuming /api/predict/live, /api/predict, and /api/health
├── App.jsx                     # Core state management, geolocation handler, and responsive layout
├── index.css                   # Custom glassmorphism design system & responsive media queries
└── main.jsx                    # Vite application entry point
```

---

## 3. Key Dashboard Features

1. **Location Selection & Telemetry Fetching**:
   - Accepts manual latitude and longitude coordinates.
   - Quick-select presets for major metropolitan areas (Bengaluru, Delhi, Mumbai, Coimbatore, Chennai, Hyderabad, Kolkata).
   - One-click browser GPS positioning (`navigator.geolocation`).
2. **AI AQI Prediction Display**:
   - Real-time numerical AQI output from the champion `GradientBoostingRegressor`.
   - Color-coded severity ring and category badge (Good, Moderate, Unhealthy, Poor, Hazardous).
   - Contextual health advisory recommendations.
   - Model provenance badge displaying active algorithm metrics ($R^2 = 0.99$).
3. **Multi-Pollutant Telemetry**:
   - Normalized metrics for PM2.5 ($\mu\text{g/m}^3$), PM10 ($\mu\text{g/m}^3$), CO ($\text{mg/m}^3$), NO2 ($\mu\text{g/m}^3$), SO2 ($\mu\text{g/m}^3$), and O3 ($\mu\text{g/m}^3$).
4. **Meteorological Status**:
   - Ambient temperature ($^\circ\text{C}$), relative humidity ($\%$), wind speed ($\text{km/h}$), and atmospheric pressure ($\text{hPa}$).
5. **Interactive Visualizations**:
   - Recharts bar chart for pollutant concentrations.
   - Half-dial radial gauge for AQI scale.
6. **State & Error Handling**:
   - Non-blocking asynchronous loading state.
   - Informative error banners with retry triggers.

---

## 4. How to Run the Application

### 1. Start the Backend (FastAPI)
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Start the Frontend (Vite)
```powershell
cd frontend
npm run dev
```
Dashboard available at: `http://localhost:3000`

### 3. Production Build
```powershell
cd frontend
npm run build
```

---

## 5. Automated Verification & Regression

- **Frontend Production Build**: `vite build` completed with 0 errors.
- **Backend Test Suite**: `29/29 PASSED` (Phase 4: 5, Phase 5: 4, Phase 6: 13, Phase 7: 7).
