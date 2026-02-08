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
echo   F8  - Start macro
echo   F9  - Emergency stop
echo   F10 - Emergency stop
echo.
echo ========================================
echo.

REM Try "python" first, then "py -3" (Windows Python Launcher)
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :found
)

py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3"
    goto :found
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :found
)

echo [ERROR] Python is not installed or not in PATH!
echo Please run "1_install.bat" first.
echo If Python is installed, check "Add Python to PATH" and restart PC.
echo.
pause
exit /b 1

:found
REM Run program
%PYTHON_CMD% main.py

echo.
echo Program terminated.
pause
