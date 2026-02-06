@echo off
chcp 65001 >nul
title 옵션 감지 매크로

echo ========================================
echo   옵션 감지 매크로 실행 중...
echo ========================================
echo.
echo 프로그램 창이 뜨면 이 창은 최소화하세요.
echo 매크로 사용 중에는 이 창을 닫지 마세요!
echo.
echo 핫키:
echo   F7  - 인식 영역 설정
echo   F8  - 매크로 시작/정지
echo   F9  - 긴급 정지
echo   F10 - 긴급 정지
echo.
echo ========================================
echo.

REM Python 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되어 있지 않습니다!
    echo "1_의존성설치.bat" 파일을 먼저 실행하세요.
    echo.
    pause
    exit /b 1
)

REM 프로그램 실행
python main.py

echo.
echo 프로그램이 종료되었습니다.
pause
