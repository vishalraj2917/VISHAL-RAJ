# AI Air Quality Prediction System

An end-to-end Machine Learning and Full-Stack Web Application designed to monitor real-time air quality metrics, predict Air Quality Index (AQI) levels using supervised machine learning models, and deliver actionable health advisories, dynamic visualizations, and AI assistance.

---

## 🚀 Main Features

### 👤 User & Dashboard Features
- **Real-time Air Quality & Weather:** Live monitoring of PM2.5, PM10, CO, NO2, SO2, O3, Temperature, Humidity, Wind Speed, and Pressure.
- **AI AQI Prediction:** Machine Learning predictions with continuous numerical AQI and standard health categorization.
- **AI Insights & Smart Recommendations:** Automated diagnostic synthesis of dominant pollutants, trajectory trends, outdoor activity limits, and mask recommendations.
- **User Authentication & Accounts:** Secure registration, login, JWT token auth, user profile management, password updates, and prediction history isolation.
- **Historical Analytics:** Chronological Recharts time series, 30-day summaries, and persistent prediction ledgers.
- **Simulation Parameter Predictor:** Custom 21-feature interactive sandbox for testing arbitrary atmospheric scenarios.
- **AI Health Advisor & Chatbot:** Context-aware conversational assistant and personalized activity advice.

### 🛡️ System & Architecture
- **Production ML Inference:** High-performance Gradient Boosting Regressor model pipeline ($R^2 = 0.99$).
- **PostgreSQL 17 Integration:** Structured SQLAlchemy 2.0 ORM persistence with Alembic migrations and tenant isolation.
- **Health & Readiness Probes:** Liveness (`/api/health`) and readiness (`/api/ready`) endpoints.
- **Containerization Ready:** Multi-container `docker-compose.yml` with healthchecks for PostgreSQL, FastAPI backend, and Nginx frontend.

---

## 🛠️ Technology Stack

- **Frontend:** React 18, Vite, Axios, Recharts, Lucide-React
- **Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, PyJWT, Passlib, Bcrypt
- **Database:** PostgreSQL 17 (Alembic migrations)
- **Machine Learning:** Scikit-learn (GradientBoostingRegressor), Pandas, NumPy, Joblib
- **Containerization:** Docker, Docker Compose, Nginx Alpine

---

## 📁 Folder Structure

```text
ai air quality prediction/
├── backend/              # FastAPI REST API, auth & ML inference services
│   ├── app/
│   │   ├── models/       # SQLAlchemy ORM models (User, Prediction, Location)
│   │   ├── routers/      # API route handlers (auth, predict, insights, analytics)
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── services/     # PredictionService, AIInsightsService, AnalyticsService
│   │   └── utils/        # Security, password hashing, AQI categorization
│   └── tests/            # Pytest test suite (63/63 passing tests)
├── frontend/             # React (Vite) Single Page Application
│   ├── src/
│   │   ├── components/   # Dashboard cards, auth modals & charts
│   │   ├── context/      # AuthContext session management
│   │   └── services/     # Axios API client with JWT interceptor
├── ml/                   # Model training, dataset processing, and evaluation pipelines
├── models/               # Serialized artifacts (best_model.joblib, preprocessor.joblib)
├── data/                 # Raw and processed chronological train/val/test splits
├── docs/                 # Detailed architectural documentation (Phases 1–13)
├── docker-compose.yml    # Multi-container orchestration
└── README.md
```

---

## 🌐 Real-World Deployment

For detailed production deployment instructions across low-cost cloud providers (Vercel, Render, Neon/Supabase), see the comprehensive [Production Deployment Guide](file:///docs/production-deployment.md).

### Local Development
```powershell
# 1. Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 2. Frontend
cd frontend
npm install
npm run dev
```

### Production Bare-Metal Startup
```powershell
# Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

# Frontend
cd frontend
npm run build
```

### Running via Docker Compose
```powershell
docker compose build
docker compose up -d
```

### Automated Testing
```powershell
$env:PYTHONPATH=".;backend"
backend\.venv\Scripts\pytest.exe backend/tests -v
```
All **63/63 tests passing**.
