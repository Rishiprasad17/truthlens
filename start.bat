@echo off
title TruthLens
color 0A
cls

echo.
echo  ============================================
echo   TruthLens - AI Trust and Evaluation Layer
echo   v0.4.0
echo  ============================================
echo.

:: ── Check Python ──────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo.
    echo  Please install Python from: https://python.org/downloads
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
echo  [OK] Python found

:: ── Check Node ────────────────────────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found.
    echo.
    echo  Please install Node.js from: https://nodejs.org
    echo.
    pause
    exit /b 1
)
echo  [OK] Node.js found

:: ── Check Ollama ──────────────────────────────────────────────────────────────
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo  [!!] Ollama is not running.
    echo.
    echo  Starting Ollama...
    start "" "ollama" serve
    echo  Waiting for Ollama to start...
    timeout /t 5 /nobreak >nul
    
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if errorlevel 1 (
        echo  [ERROR] Could not start Ollama.
        echo.
        echo  Please:
        echo    1. Install Ollama from: https://ollama.ai
        echo    2. Run: ollama pull llama3
        echo    3. Run this file again
        echo.
        pause
        exit /b 1
    )
)
echo  [OK] Ollama is running

:: ── Install Python packages if needed ─────────────────────────────────────────
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo  [->] Installing Python packages...
    pip install -r requirements.txt --quiet
    echo  [OK] Python packages installed
) else (
    echo  [OK] Python packages ready
)

:: ── Install dashboard packages if needed ──────────────────────────────────────
if not exist "dashboard\node_modules" (
    echo  [->] Installing dashboard packages (first time only, takes 1-2 min)...
    cd dashboard
    call npm install --silent
    cd ..
    echo  [OK] Dashboard packages installed
) else (
    echo  [OK] Dashboard packages ready
)

:: ── Check if ports are free ───────────────────────────────────────────────────
netstat -ano | findstr ":8000 " >nul 2>&1
if not errorlevel 1 (
    echo  [!!] Port 8000 already in use. Killing old process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do taskkill /PID %%a /F >nul 2>&1
    timeout /t 2 /nobreak >nul
)

netstat -ano | findstr ":8001 " >nul 2>&1
if not errorlevel 1 (
    echo  [!!] Port 8001 already in use. Killing old process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001 "') do taskkill /PID %%a /F >nul 2>&1
    timeout /t 2 /nobreak >nul
)

netstat -ano | findstr ":5173 " >nul 2>&1
if not errorlevel 1 (
    echo  [!!] Port 5173 already in use. Killing old process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 "') do taskkill /PID %%a /F >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:: ── Start API server ──────────────────────────────────────────────────────────
echo.
echo  [->] Starting TruthLens API...
start "TruthLens API" /min cmd /c "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000"

:: Wait for API to be ready
echo  [->] Waiting for API to be ready...
:wait_api
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 goto wait_api
echo  [OK] API running at http://localhost:8000

:: ── Start Proxy server ────────────────────────────────────────────────────────
echo  [->] Starting TruthLens Proxy...
start "TruthLens Proxy" /min cmd /c "python -m uvicorn proxy.server:app --host 0.0.0.0 --port 8001"
timeout /t 3 /nobreak >nul
echo  [OK] Proxy running at http://localhost:8001

:: ── Start Dashboard ───────────────────────────────────────────────────────────
echo  [->] Starting Dashboard...
start "TruthLens Dashboard" /min cmd /c "cd dashboard && npm run dev"
timeout /t 4 /nobreak >nul
echo  [OK] Dashboard running at http://localhost:5173

:: ── Open browser ──────────────────────────────────────────────────────────────
echo  [->] Opening browser...
start "" "http://localhost:5173"

:: ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo  ============================================
echo   TruthLens is running!
echo  ============================================
echo.
echo   Dashboard  ->  http://localhost:5173
echo   API        ->  http://localhost:8000
echo   Proxy      ->  http://localhost:8001
echo   API Docs   ->  http://localhost:8000/docs
echo.
echo   To stop TruthLens, close this window
echo   or press any key.
echo.
echo  ============================================
echo.
pause

:: ── Stop everything when user presses a key ──────────────────────────────────
echo  Stopping TruthLens...
taskkill /FI "WINDOWTITLE eq TruthLens API" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq TruthLens Proxy" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq TruthLens Dashboard" /F >nul 2>&1
echo  Done. Goodbye.
timeout /t 2 /nobreak >nul
