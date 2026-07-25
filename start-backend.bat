@echo off
echo ============================================
echo   TeamFlow AI - Starting Backend Server
echo ============================================

cd /d d:\GENAI\TeamFlow-AI\backend

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting FastAPI backend on http://localhost:8000
echo API Docs: http://localhost:8000/api/docs
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
