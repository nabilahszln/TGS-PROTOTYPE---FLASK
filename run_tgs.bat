@echo off
title Troubleshooting Guide System - Auto Setup & Run
color 0B

echo.
echo ========================================
echo  TROUBLESHOOTING GUIDE SYSTEM (TGS)
echo  Auto Setup and Run Script
echo ========================================
echo.

:: Check if Python is installed
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
) else (
    python --version
    echo Python found successfully!
)

echo.
echo [2/4] Installing required packages...
echo This may take a few minutes...

:: Upgrade pip first
python -m pip install --upgrade pip

:: Install required packages
python -m pip install Flask pandas openpyxl

:: Check installation
echo.
echo [3/4] Verifying installation...
python -c "import flask, pandas, openpyxl; print('All packages installed successfully!')" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Some packages may not be installed correctly
    echo Attempting to install again...
    pip install Flask pandas openpyxl
)

echo.
echo [4/4] Starting Troubleshooting Guide System...
echo.
echo ==========================================
echo  System is starting up...
echo  
echo  Once running, open your web browser and go to:
echo  http://localhost:5000
echo  
echo  Press Ctrl+C to stop the server
echo ==========================================
echo.

:: Wait a moment before starting
timeout /t 3 /nobreak >nul

:: Start the Flask application
python app.py

:: If we reach here, the app has stopped
echo.
echo ==========================================
echo  Application has stopped.
echo ==========================================
pause