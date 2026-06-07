@echo off
title TruthLens - Stop
echo.
echo  Stopping TruthLens...
echo.

taskkill /FI "WINDOWTITLE eq TruthLens API" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq TruthLens Proxy" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq TruthLens Dashboard" /F >nul 2>&1

:: Also kill by port just in case
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001 "') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 "') do taskkill /PID %%a /F >nul 2>&1

echo  [OK] TruthLens stopped.
echo.
timeout /t 2 /nobreak >nul
