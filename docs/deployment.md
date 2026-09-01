# Deployment & Operations Guide — AI Air Quality Prediction System

## 1. Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 17 running on localhost:5432

### Backend Setup
```powershell
cd backend
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server with live reload
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

---

## 2. Production Startup (Bare Metal / Host OS)

### Backend Production Server
```powershell
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

### Frontend Production Build
```powershell
cd frontend
npm run build
# The optimized bundle is generated in the dist/ folder, ready for serving via Nginx or static file server
```

---

## 3. Docker Container Deployment

### Orchestration with Docker Compose
```powershell
# Build container images
docker compose build

# Start services in detached mode
docker compose up -d

# Verify container health status
docker compose ps

# Stop and tear down services
docker compose down
```

---

## 4. Environment Variables Configuration

### Backend (`backend/.env`)
```ini
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:password@localhost:5432/ai_air_quality
SECRET_KEY=replace-with-a-secure-random-32-byte-hex-secret-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ENABLE_DOCS=true
```

### Frontend (`frontend/.env`)
```ini
VITE_API_URL=http://127.0.0.1:8000
```

---

## 5. Troubleshooting & Diagnostics

- **Database Connectivity**: Verify PostgreSQL is running on port 5432 and `pg_isready` reports success. Run `alembic current` to check migration state.
- **ML Artifacts**: Ensure `models/best_model.joblib` and `models/preprocessor.joblib` are present. Check `/api/ready` for memory status.
- **Authentication 401 Expiry**: The frontend automatically intercepts expired JWTs, clears local storage, and prompts re-login without infinite reload loops.
