@echo off
chcp 65001 >nul
title 옵션 감지 매크로 - 의존성 설치

echo ========================================
echo   옵션 감지 매크로 - 의존성 설치
echo ========================================
echo.
echo Python 패키지를 설치합니다...
echo 인터넷 연결이 필요하며, 약 2~3분 소요됩니다.
echo.

REM Python이 설치되어 있는지 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되어 있지 않습니다!
    echo.
    echo Python 설치 방법:
    echo 1. https://www.python.org/downloads/ 방문
    echo 2. 최신 버전 다운로드 및 설치
    echo 3. 설치 시 "Add Python to PATH" 체크 필수!
    echo.
    pause
    exit /b 1
)

echo [1/1] 필요한 패키지 설치 중...
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   ✓ 설치 완료!
    echo ========================================
    echo.
    echo 이제 "2_매크로실행.bat" 파일을 실행하세요!
    echo.
) else (
    echo.
    echo [오류] 설치 중 문제가 발생했습니다.
    echo 인터넷 연결을 확인하고 다시 시도해주세요.
    echo.
)

pause
