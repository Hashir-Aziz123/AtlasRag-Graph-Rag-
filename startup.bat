@echo off
TITLE GraphRAG Command Center
COLOR 0A

echo ===================================================
echo      INITIALIZING K-FORGE GRAPHRAG PLATFORM
echo ===================================================
echo.

echo [*] Phase 1: Booting Database Infrastructure...
cd docker
docker compose up -d
cd ..
echo [OK] Docker containers are running.
echo.

echo [*] Phase 2: Launching Microservices...

:: Start the FastAPI Server (Command Center)
start "FastAPI Server" cmd /k "COLOR 0E && echo [*] Starting Uvicorn API... && call venv\Scripts\activate && uvicorn src.api.v1.main:app --reload --port 8000"

:: Start the Celery Worker (The Muscle)
start "Celery Worker" cmd /k "COLOR 0B && echo [*] Starting Celery Worker... && call venv\Scripts\activate && celery -A src.workers.workers worker --loglevel=info --pool=solo"

:: Start Celery Beat (The Scheduler)
start "Celery Beat" cmd /k "COLOR 0D && echo [*] Starting Celery Beat Scheduler... && call venv\Scripts\activate && celery -A src.workers.workers beat --loglevel=info"

echo [OK] All services have been launched in separate windows.
echo.
echo You can close this master window. The services will remain running.
pause