@echo off
cd /d "%~dp0"
title Option Detector Macro

echo ========================================
echo   Starting Option Detector Macro...
echo ========================================
echo.
echo Program window will open soon.
echo Do NOT close this black window while using the program!
echo Just minimize this window.
echo.
echo Hotkeys:
echo   F7  - Set recognition area
echo   F8  - Start/Stop macro
echo   F9  - Emergency stop
echo   F10 - Emergency stop
echo.
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please run "1_install.bat" first.
    echo.
    pause
    exit /b 1
)

REM Run program
python main.py

echo.
echo Program terminated.
pause
