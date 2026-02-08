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
echo.
echo Please install Python first:
echo 1. Visit https://www.python.org/downloads/
echo 2. Download and install latest version
echo 3. IMPORTANT: Check "Add Python to PATH" during installation
echo.
echo If Python is already installed, try:
echo - Restart your computer after installation
echo - Or run this file by right-click and "Run as administrator"
echo.
pause
exit /b 1

:found
echo [OK] Python found: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

echo [1/1] Installing required packages...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt

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
