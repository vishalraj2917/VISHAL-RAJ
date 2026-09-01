# Phase 22: Automated Cloud Deployment & Authentication Playbook

## 1. System Status & Verification Summary

The **AI Air Quality Prediction** project has successfully completed local initialization, git repository tracking, and regression validation:

```text
               [End User Client]
                       │
                       │ HTTPS
                       ▼
          [Vercel Frontend (React 18 / Vite)]
     - Production Bundle: dist/ (Vite build: 0 errors)
     - Target Env: VITE_API_URL=<Render Backend URL>
                       │
                       │ REST API / Bearer JWT
                       ▼
          [Render FastAPI Backend Service]
     - Runtime: Python 3.11+, Uvicorn
     - Build: pip install -r requirements.txt && alembic upgrade head
     - ML Champion: models/best_model.joblib (446 KB)
                       │
                       │ SSL Connection (sslmode=require)
                       ▼
           [Neon Serverless PostgreSQL 17]
     - Database: ai_air_quality
     - Migration Head: ae0f4850fca9 (head)
```

---

## 2. Local Environment Automated Actions Completed in Phase 22

1. **Vercel CLI**: Installed officially via npm (`Vercel CLI 59.10.0`).
2. **Git Repository**: Initialized locally on `main` branch with complete project history.
3. **Model Artifacts & Codebase**: 134 files (including ML models and preprocessors) committed clean to Git.
4. **Security Filters**: Verified `.env`, `.env.*`, `.venv`, and `node_modules` are properly ignored by `.gitignore`.
5. **Backend Tests**: 68/68 test cases passing.
6. **Frontend Build**: Vite production build succeeded in 5.32s with zero errors.
7. **Database Migrations**: Verified Alembic head is `ae0f4850fca9 (head)`.

---

## 3. Production Environment Variables Reference (Non-Secret)

### Render Web Service Settings
| Key | Purpose / Description |
| :--- | :--- |
| `DATABASE_URL` | Neon PostgreSQL connection string (`?sslmode=require`) |
| `SECRET_KEY` | 32+ char random hex string for server sessions |
| `JWT_SECRET_KEY` | 32+ char random hex string for JWT tokens |
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |
| `CORS_ORIGINS` | `https://<YOUR_VERCEL_DOMAIN>.vercel.app` |
| `ENABLE_DOCS` | `false` |

### Vercel Frontend Settings
| Key | Value |
| :--- | :--- |
| `VITE_API_URL` | `https://<YOUR_RENDER_DOMAIN>.onrender.com` |

---

## 4. Final Browser Authorization Steps Required

The application is fully committed and ready for instantaneous deployment. Complete the following 4 cloud account authorizations:

### Action A — GitHub Remote Push
1. Create a new repository on [GitHub.com](https://github.com/new) named `ai-air-quality-prediction`.
2. Push the local commits:
   ```powershell
   git remote add origin https://github.com/<YOUR_USERNAME>/ai-air-quality-prediction.git
   git push -u origin main
   ```

### Action B — Neon PostgreSQL Creation
1. Go to [Neon.tech](https://neon.tech) and create a project/database named `ai_air_quality`.
2. Copy the connection string: `postgresql://[user]:[pass]@[endpoint].neon.tech/ai_air_quality?sslmode=require`.

### Action C — Render Backend Service Creation
1. Go to [Render.com](https://render.com) -> **New +** -> **Web Service** -> select your GitHub repository.
2. Root Directory: `backend`
3. Build Command: `pip install -r requirements.txt && alembic upgrade head`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
5. Paste environment variables (`DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, `ENVIRONMENT=production`, `CORS_ORIGINS`).

### Action D — Vercel Frontend Deployment
1. Go to [Vercel.com](https://vercel.com) -> **Add New Project** -> select your GitHub repository.
2. Root Directory: `frontend`
3. Framework: `Vite`
4. Add environment variable: `VITE_API_URL=https://<YOUR_RENDER_DOMAIN>.onrender.com`
5. Click **Deploy**.
