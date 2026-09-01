# Phase 18: Live Cloud Deployment & Operations Master Guide

## 1. System Architecture & Component Mapping

```text
       [End User Browser / Mobile Client]
                       │
                       │ HTTPS (TLS 1.3)
                       ▼
          [Vercel Frontend React SPA]
     - Domain: https://<your-vercel-domain>.vercel.app
     - Built with Vite, React 18, Chart.js, Lucide Icons
     - Environment Variable: VITE_API_URL=https://<your-render-domain>.onrender.com
                       │
                       │ REST API / Bearer JWT Authorization
                       ▼
          [Render FastAPI Web Service]
     - Domain: https://<your-render-domain>.onrender.com
     - Python 3.11+, Uvicorn 2 workers
     - ML Inference Singleton (backend/models/best_model.joblib)
     - Strict CORS Whitelist: https://<your-vercel-domain>.vercel.app
                       │
                       │ SSL Connection (sslmode=require)
                       ▼
           [Neon Serverless PostgreSQL]
     - Database: ai_air_quality
     - Managed PostgreSQL 17
     - Automatic Alembic Migrations: ae0f4850fca9 (head)
```

---

## 2. Step-by-Step Production Deployment Guide

### STEP 1 — Git & GitHub Initialization
Run the following commands in PowerShell from the project root:
```powershell
# 1. Initialize local repository
git init

# 2. Stage safe files (ML models tracked, .env/.venv/node_modules ignored)
git add .

# 3. Create initial commit
git commit -m "feat: complete Phase 1-18 production ready AI Air Quality Prediction system"

# 4. Set default branch to main
git branch -M main

# 5. Add your remote GitHub repository and push
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY_NAME>.git
git push -u origin main
```

---

### STEP 2 — Provision Neon PostgreSQL Database
1. Go to [Neon.tech](https://neon.tech) and log in or register.
2. Click **Create Project** and specify the database name `ai_air_quality`.
3. In the Neon Console, copy the connection string with SSL mode enabled:
   `postgresql://[user]:[password]@[ep-xyz].neon.tech/ai_air_quality?sslmode=require`
4. **Security Notice**: Never commit this connection string to any public repository or share the credentials.

---

### STEP 3 — Deploy FastAPI Backend to Render
1. Go to [Render.com](https://render.com) and log in.
2. Click **New +** -> **Web Service** and connect your GitHub repository.
3. Configure the web service settings:
   - **Name**: `ai-air-quality-api`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
4. Configure Environment Variables:
   - `DATABASE_URL`: *(Your Neon PostgreSQL connection string)*
   - `SECRET_KEY`: *(Cryptographically secure random 32+ character hex string)*
   - `JWT_SECRET_KEY`: *(Cryptographically secure random 32+ character hex string)*
   - `ENVIRONMENT`: `production`
   - `LOG_LEVEL`: `INFO`
   - `CORS_ORIGINS`: `https://<YOUR_VERCEL_DOMAIN>.vercel.app` (or temporary placeholder)
   - `ENABLE_DOCS`: `false`
5. Click **Create Web Service**.
6. When deployment finishes, copy your Render domain (`https://<YOUR_RENDER_DOMAIN>.onrender.com`).

---

### STEP 4 — Deploy React Frontend to Vercel
1. Go to [Vercel.com](https://vercel.com) and click **Add New...** -> **Project**.
2. Select your GitHub repository.
3. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add Environment Variable:
   - `VITE_API_URL`: `https://<YOUR_RENDER_DOMAIN>.onrender.com`
5. Click **Deploy**.
6. Copy your live Vercel domain (`https://<YOUR_VERCEL_DOMAIN>.vercel.app`).

---

### STEP 5 — Finalize CORS on Render
1. Open your Render Dashboard -> select `ai-air-quality-api` -> **Environment**.
2. Update `CORS_ORIGINS` to match your exact Vercel URL:
   `CORS_ORIGINS=https://<YOUR_VERCEL_DOMAIN>.vercel.app`
3. Save changes. Render will automatically re-deploy/apply environment updates without downtime.

---

## 3. Production Health & Endpoint Verification Checklist

Once deployed, verify the endpoints using `curl` or browser:

| Endpoint | Method | Expected Output |
| :--- | :--- | :--- |
| `/api/health` | GET | `{"status": "ok", "database": "connected", "ml_model": "ready"}` |
| `/api/ready` | GET | `{"status": "ready", "database": "ok", "ml_model": "ok"}` |
| `/api/auth/register` | POST | Creates user, sets password hash, returns user payload |
| `/api/auth/login` | POST | Returns JWT bearer access token |
| `/api/predict` | POST | Returns AQI prediction, category, and pollutant breakdown |
| `/api/predict/live` | POST | Retrieves real-time Open-Meteo data, feeds ML pipeline, returns AQI forecast |
| `/api/insights` | GET/POST | Generates localized health advisories and pollution mitigation actions |
| `/api/analytics/summary`| GET | Returns user-isolated prediction history aggregates and trends |

---

## 4. Troubleshooting & Operational Runbook

1. **Database Migration Failures**:
   - Verify `DATABASE_URL` contains `?sslmode=require`.
   - Run manual migration if needed: `alembic upgrade head`.

2. **CORS Blocked Requests in Browser**:
   - Ensure Render's `CORS_ORIGINS` strictly matches the Vercel scheme and hostname (no trailing slash, e.g. `https://my-app.vercel.app`).

3. **ML Model Loading Issues**:
   - Ensure `models/best_model.joblib` and `models/preprocessor.joblib` were pushed to the GitHub repository and are present in the build directory.
