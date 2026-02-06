@echo off
cd /d "%~dp0"
title Option Detector Macro - Install Dependencies

echo ========================================
echo   Installing Dependencies...
echo ========================================
echo.
echo This will install required packages.
echo Internet connection required (2-3 min)
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python first:
    echo 1. Visit https://www.python.org/downloads/
    echo 2. Download and install latest version
    echo 3. IMPORTANT: Check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [1/1] Installing required packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Installation Complete!
    echo ========================================
    echo.
    echo Now run "2_run.bat" to start the program!
    echo.
) else (
    echo.
    echo [ERROR] Installation failed.
    echo Please check your internet connection and try again.
    echo.
)

pause
