@echo off
echo Starting AI Air Quality Prediction Platform...
echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000
start "AQI Backend API" cmd /k "cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo [2/2] Launching Vite Frontend on http://localhost:3000
start "AQI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Platform successfully launched!
echo Access Web Application: http://localhost:3000
echo Access API Documentation: http://127.0.0.1:8000/docs
