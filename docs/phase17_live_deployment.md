# Phase 17: Live Cloud Deployment Master Playbook

## 1. Production Architecture Overview

The system is configured for cloud deployment across the following stack:
- **Managed Database**: PostgreSQL 17 on **Neon.tech**
- **FastAPI Web Service**: **Render.com** (Linux Web Service / Python 3)
- **Frontend SPA**: **Vercel** (Static React 18 / Vite deployment)

```text
  [Vercel Frontend] (https://<your-vercel-domain>)
         │
         │ HTTPS / REST (JWT Bearer Auth)
         ▼
  [Render Backend]  (https://<your-render-domain>)
  - Python 3.11+, FastAPI, Uvicorn (0.0.0.0:$PORT)
  - Singleton ML Model (Gradient Boosting)
  - Strict CORS whitelist
         │
         │ SSL Connection (sslmode=require)
         ▼
  [Neon PostgreSQL] (postgresql://user:pass@ep-xyz.neon.tech/ai_air_quality?sslmode=require)
  - Managed PostgreSQL 17
  - Automatic Alembic Migrations
```

---

## 2. Step-by-Step Deployment Instructions

### Part A — Provision Neon PostgreSQL Database
1. Go to [Neon.tech](https://neon.tech) and register for a free account.
2. Create a new PostgreSQL database named `ai_air_quality`.
3. In the Neon Dashboard, copy the **Connection String** with `sslmode=require`.
   *(Format: `postgresql://[user]:[password]@[endpoint].neon.tech/ai_air_quality?sslmode=require`)*
4. **Keep this connection string private** (do not commit or paste in chat).

---

### Part B — Deploy Backend on Render
1. Go to [Render.com](https://render.com) and sign in.
2. Click **New +** -> **Web Service** and connect your GitHub repository.
3. Configure the service settings:
   - **Name**: `ai-air-quality-api`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
4. Add **Environment Variables**:
   | Key | Value Description |
   | :--- | :--- |
   | `DATABASE_URL` | Your Neon PostgreSQL connection string from Part A |
   | `SECRET_KEY` | Generate a 32-character random hex string for JWT hashing |
   | `JWT_SECRET_KEY` | Same 32-character string |
   | `ENVIRONMENT` | `production` |
   | `LOG_LEVEL` | `INFO` |
   | `CORS_ORIGINS` | `https://<your-vercel-domain>` (e.g. `http://localhost:3000` temporarily) |
   | `ENABLE_DOCS` | `false` (or `true` if public Swagger docs are desired) |
5. Click **Create Web Service**.
6. Once deployed, verify your endpoints:
   - `https://<your-render-domain>/api/health` -> returns `{"status":"ok", "database":"connected", "ml_model":"ready"}`
   - `https://<your-render-domain>/api/ready` -> returns `{"status":"ready", "database":"ok", "ml_model":"ok"}`

---

### Part C — Deploy Frontend on Vercel
1. Go to [Vercel.com](https://vercel.com) and link your GitHub repository.
2. Configure build settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add **Environment Variable**:
   | Key | Value |
   | :--- | :--- |
   | `VITE_API_URL` | `https://<your-render-domain>` |
4. Click **Deploy**.
5. Once deployment completes, copy your live frontend domain:
   `https://<your-vercel-domain>`

---

### Part D — Configure Production CORS on Render
1. In the Render Dashboard -> `ai-air-quality-api` -> **Environment**.
2. Update `CORS_ORIGINS`:
   `CORS_ORIGINS=https://<your-vercel-domain>`
3. Save changes (Render will automatically apply and restart the service).

---

### Part E — End-to-End Live Validation Checklist
1. Open `https://<your-vercel-domain>`.
2. Click **Register** and create a new user account.
3. Verify automatic authentication and dashboard rendering.
4. Click **Use GPS Coordinates** or select a city to generate a live AQI forecast.
5. Verify that predicted AQI, pollutant breakdown, and health advice render properly.
6. Check **Prediction Ledger Table** to confirm database persistence.
7. Review **AI Air Quality Insights & Recommendations** panel.
8. Click **Account Settings** and test password update.
9. Click **Logout** and verify unauthenticated access rejection on protected operations.

---

## 3. Verification Summary

- **Local Regression Suite**: **68/68 tests PASSING**.
- **Frontend Production Build**: `npm run build` executed with **0 errors**.
- **Database Schema**: Managed by Alembic with clean migration head `ae0f4850fca9`.
- **Security Audit**: No secrets in source code; `.env` is gitignored; direct salted bcrypt hashing implemented.
