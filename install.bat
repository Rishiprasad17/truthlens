@echo off
title TruthLens Installer
color 0A
cls

echo.
echo  ============================================
echo   TruthLens Installer - v0.4.0
echo  ============================================
echo.
echo  This will install TruthLens on your computer.
echo  Estimated time: 2-5 minutes.
echo.
pause

:: ── Check Python ──────────────────────────────────────────────────────────────
echo  Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Python not found!
    echo.
    echo  Please install Python:
    echo    1. Go to: https://python.org/downloads
    echo    2. Download Python 3.10 or newer
    echo    3. IMPORTANT: Check "Add Python to PATH" during install
    echo    4. Run this installer again
    echo.
    start "" "https://python.org/downloads"
    pause
    exit /b 1
)
echo  [OK] Python found

:: ── Check Node ────────────────────────────────────────────────────────────────
echo  Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Node.js not found!
    echo.
    echo  Please install Node.js:
    echo    1. Go to: https://nodejs.org
    echo    2. Download the LTS version
    echo    3. Run this installer again
    echo.
    start "" "https://nodejs.org"
    pause
    exit /b 1
)
echo  [OK] Node.js found

:: ── Check Ollama ──────────────────────────────────────────────────────────────
echo  Checking Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [!!] Ollama not found.
    echo.
    echo  Ollama lets TruthLens run AI models on your computer for free.
    echo  Please install it:
    echo    1. Go to: https://ollama.ai
    echo    2. Download and install Ollama
    echo    3. Run this installer again
    echo.
    start "" "https://ollama.ai"
    pause
    exit /b 1
)
echo  [OK] Ollama found

:: ── Install Python packages ───────────────────────────────────────────────────
echo.
echo  Installing Python packages...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install Python packages.
    echo  Try running: pip install -r requirements.txt
    pause
    exit /b 1
)
echo  [OK] Python packages installed

:: ── Install dashboard ─────────────────────────────────────────────────────────
echo  Installing dashboard packages (this may take 1-2 minutes)...
cd dashboard
call npm install --silent
if errorlevel 1 (
    echo  [ERROR] Failed to install dashboard packages.
    pause
    exit /b 1
)
cd ..
echo  [OK] Dashboard installed

:: ── Pull Ollama model ─────────────────────────────────────────────────────────
echo.
echo  Checking for AI models...
ollama list | findstr "llama3" >nul 2>&1
if errorlevel 1 (
    echo  Downloading llama3 model (about 4GB, this will take a few minutes)...
    echo  Please wait...
    ollama pull llama3
    echo  [OK] llama3 model downloaded
) else (
    echo  [OK] AI model ready
)

:: ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo  ============================================
echo   Installation complete!
echo  ============================================
echo.
echo   To start TruthLens:
echo     Double-click START.BAT
echo.
echo   Or open this folder and double-click start.bat
echo.
echo  ============================================
echo.
pause
