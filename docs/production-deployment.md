# Production Deployment Guide — Real-World Cloud & Container Setup

## 1. Production Architecture Overview

The system is architected for low-cost, scalable cloud hosting:

```text
┌────────────────────────────────────────────────────────┐
│               Frontend Static Hosting                  │
│             (Vercel / Netlify / Cloudflare)            │
│  - Serves compiled React 18 / Vite bundle              │
│  - Configured with VITE_API_URL                        │
└───────────────────────────┬────────────────────────────┘
                            │ HTTPS / REST (JWT Auth)
                            ▼
┌────────────────────────────────────────────────────────┐
│            Backend Cloud Application Service           │
│              (Render / Railway / Fly.io)               │
│  - FastAPI production web server (uvicorn)             │
│  - In-memory ML inference (Gradient Boosting)          │
│  - Automatic CORS origin whitelist                     │
│  - Healthchecks on /api/health and /api/ready          │
└───────────────────────────┬────────────────────────────┘
                            │ SSL / Connection Pool
                            ▼
┌────────────────────────────────────────────────────────┐
│             Managed Cloud PostgreSQL 17                │
│              (Neon / Supabase / Render)                │
│  - Multi-tenant isolated storage                       │
│  - Alembic automated migrations                        │
└────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Deployment Instructions

### Step 1: Provision Managed PostgreSQL
1. Create a free managed database on [Neon.tech](https://neon.tech) or [Supabase.com](https://supabase.com).
2. Copy the connection string (`postgresql://user:pass@ep-host.region.neon.tech/ai_air_quality?sslmode=require`).

### Step 2: Deploy FastAPI Backend (Render.com)
1. Link your GitHub repository to Render as a **Web Service**.
2. Set the following environment configurations:
   - **Environment**: `Python 3`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
3. Add Environment Variables:
   - `DATABASE_URL`: Your managed PostgreSQL URL from Step 1.
   - `SECRET_KEY`: Generate a 32-character random string.
   - `ENVIRONMENT`: `production`
   - `CORS_ORIGINS`: `https://your-frontend-domain.vercel.app`
   - `ENABLE_DOCS`: `false` (or `true` if public Swagger docs are desired).
4. Deploy service and copy your backend URL (`https://ai-air-quality-api.onrender.com`).

### Step 3: Deploy React Frontend (Vercel / Netlify)
1. Link repository to Vercel or Netlify.
2. Configure build settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add Environment Variable:
   - `VITE_API_URL`: `https://ai-air-quality-api.onrender.com`
4. Deploy the application.

---

## 3. Database Migration Procedures

Run database migrations against the production instance prior to routing traffic:
```powershell
# From local terminal pointed to remote DATABASE_URL
$env:DATABASE_URL="postgresql://user:pass@host/ai_air_quality?sslmode=require"
cd backend
alembic upgrade head
```

---

## 4. Pre-Flight Security Checklist

- [x] No hardcoded passwords, database URLs, or JWT secrets in source code.
- [x] `.env` files are git-ignored and never committed.
- [x] Direct salted bcrypt password hashing with truncation limits.
- [x] Strict CORS origin validation enabled.
- [x] Global exception filter masks internal Python stack traces from 500 responses.
- [x] User-scoped predictions and historical telemetry isolation verified.
- [x] Single-pass in-memory ML model loading during application lifespan.
