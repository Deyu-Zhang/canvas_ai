@echo off
echo ========================================
echo Canvas AI Agent - Quick Start
echo ========================================
echo.

REM 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo [1/4] Checking backend dependencies...
pip install -r requirements.txt --quiet

echo [2/4] Checking frontend...
if not exist "frontend\build" (
    echo [WARNING] Frontend not built.
    echo.
    echo To build frontend:
    echo   cd frontend
    echo   npm install
    echo   npm run build
    echo.
)

echo [3/4] Starting server...
echo.
echo ========================================
echo Server Options:
echo ========================================
echo.
echo [1] Local only (http://localhost:8000)
echo [2] With LocalTunnel (public access)
echo.
set /p CHOICE="Choose option (1 or 2): "

if "%CHOICE%"=="2" (
    echo.
    echo Starting with LocalTunnel...
    python start_server.py
) else (
    echo.
    echo Starting local server only...
    python api_server.py
)

pause

