# Phase 16: Live Cloud Deployment & Operations Master Guide

## 1. Production Architecture Overview

The application is architected for zero-maintenance, low-cost cloud deployment:

```text
┌────────────────────────────────────────────────────────┐
│                   Vercel Frontend                      │
│             https://<your-vercel-domain>               │
│  - React 18 / Vite Single Page Application             │
│  - Environment: VITE_API_URL                           │
└───────────────────────────┬────────────────────────────┘
                            │ HTTPS / REST (JWT Bearer Auth)
                            ▼
┌────────────────────────────────────────────────────────┐
│                Render FastAPI Web Service              │
│              https://<your-render-domain>              │
│  - Python 3.11+, Uvicorn 0.0.0.0:$PORT                 │
│  - In-Memory Champion GradientBoostingRegressor        │
│  - Lifespan single-load artifact cache                 │
│  - Health checks on /api/health and /api/ready         │
└───────────────────────────┬────────────────────────────┘
                            │ SSL Mode = require
                            ▼
┌────────────────────────────────────────────────────────┐
│              Neon Managed PostgreSQL 17                │
│                 (ai_air_quality database)              │
│  - Automatic Alembic Migrations (ae0f4850fca9)         │
│  - Multi-tenant isolated predictions                   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Manual Cloud Deployment

### Part A: Provision Managed Database on Neon.tech
1. Open [Neon.tech](https://neon.tech) in your browser and sign in.
2. Create a project and name the database `ai_air_quality`.
3. In the Dashboard, copy the **Connection string** (PostgreSQL URI with `sslmode=require`).
4. **Keep this connection string private** — do not commit or share it.

---

### Part B: Deploy FastAPI Backend on Render.com
1. Open [Render.com](https://render.com) and click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the service:
   - **Name**: `ai-air-quality-api`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
4. Add the following **Environment Variables** in Render:
   | Key | Value Description |
   | :--- | :--- |
   | `DATABASE_URL` | Your Neon PostgreSQL connection string |
   | `SECRET_KEY` | 32-character random hex string for JWT hashing |
   | `JWT_SECRET_KEY` | Same 32-character hex string |
   | `ENVIRONMENT` | `production` |
   | `LOG_LEVEL` | `INFO` |
   | `CORS_ORIGINS` | `http://localhost:3000` *(updated to your Vercel URL in Part D)* |
   | `ENABLE_DOCS` | `false` *(or `true` if public Swagger UI is desired)* |
5. Click **Create Web Service**.
6. When deployment finishes, copy your Render URL: `https://<your-render-domain>`.
7. Verify health endpoints:
   - `https://<your-render-domain>/api/health` -> `{"status":"ok", "database":"connected", "ml_model":"ready"}`
   - `https://<your-render-domain>/api/ready` -> `{"status":"ready", "database":"ok", "ml_model":"ok"}`

---

### Part C: Deploy React Frontend on Vercel
1. Open [Vercel.com](https://vercel.com) and click **Add New...** -> **Project**.
2. Select your GitHub repository.
3. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add **Environment Variable**:
   | Key | Value |
   | :--- | :--- |
   | `VITE_API_URL` | `https://<your-render-domain>` *(your Render backend URL from Part B)* |
5. Click **Deploy**.
6. When build completes, copy your live frontend domain: `https://<your-vercel-domain>`.

---

### Part D: Update CORS Origins on Render
1. Return to the Render Dashboard -> `ai-air-quality-api` -> **Environment**.
2. Update `CORS_ORIGINS`:
   `CORS_ORIGINS=https://<your-vercel-domain>`
3. Click **Save Changes** (Render will automatically apply the changes and reload).

---

### Part E: End-to-End Live Validation Checklist
1. Open `https://<your-vercel-domain>`.
2. Click **Register** and create a user account.
3. Verify automatic session login and glassmorphic dashboard loading.
4. Click **Use GPS Coordinates** or select a city to generate a live AQI forecast.
5. Verify that AQI, pollutant breakdown, and health advice render properly.
6. Check **Prediction Ledger Table** to confirm database persistence.
7. Review **AI Air Quality Insights & Recommendations** panel.
8. Click **Account Settings** and test password update.
9. Click **Logout** and verify unauthenticated access rejection on protected operations.

---

## 3. Troubleshooting & Diagnostics

- **Database Connection Failure**: Verify the Neon database exists and that `sslmode=require` is present in `DATABASE_URL`.
- **CORS Blocked**: Ensure the exact Vercel domain (with `https://`) is present in Render's `CORS_ORIGINS` variable.
- **ML Artifacts Not Found**: Verify that `models/best_model.joblib` and `models/preprocessor.joblib` are committed in the repository (check `.gitignore`).
