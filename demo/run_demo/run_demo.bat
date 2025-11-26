@echo off
REM Military Command Control System - Demo Launcher (Windows Version)
REM Windows equivalent of Linux run_demo.sh file

setlocal enabledelayedexpansion

REM Set window title
title Military Command Control System - Demo Launcher

echo ========================================
echo    MILITARY COMMAND CONTROL SYSTEM
echo    Demo Launcher v1.0 (Windows)
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Node.js not found!
    echo Only DDS Publishers will be started.
    echo Node.js installation required for web dashboard:
    echo Download from: https://nodejs.org/
    echo.
    set "NODEJS_AVAILABLE=false"
) else (
    for /f "delims=" %%i in ('node --version') do set "NODE_VERSION=%%i"
    echo [OK] Node.js found: %NODE_VERSION%
    set "NODEJS_AVAILABLE=true"
)

REM Navigate to demo directory and detect project root
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "DEMO_DIR=%SCRIPT_DIR%\.."
set "PROJECT_ROOT=%DEMO_DIR%\.."

REM Walk up to find project root (contains IDL and scenarios)
set "CURRENT_DIR=%DEMO_DIR%"
:find_root
if exist "%CURRENT_DIR%\IDL" if exist "%CURRENT_DIR%\scenarios" (
    set "PROJECT_ROOT=%CURRENT_DIR%"
    goto :root_found
)
if "%CURRENT_DIR%"=="%CURRENT_DIR:\..=%" goto :root_found
set "CURRENT_DIR=%CURRENT_DIR%\.."
goto :find_root
:root_found

cd /d "%DEMO_DIR%"

echo Demo directory: %DEMO_DIR%
echo Project root: %PROJECT_ROOT%

REM Install dependencies if node_modules doesn't exist
if "%NODEJS_AVAILABLE%"=="true" (
    if not exist "%DEMO_DIR%\node_modules" (
        echo [INFO] Installing Node.js dependencies...
        cd /d "%DEMO_DIR%"
        call npm install
        cd /d "%DEMO_DIR%"
        if errorlevel 1 (
            echo [ERROR] Dependency installation failed!
            echo Only DDS Publishers will be started.
            set "NODEJS_AVAILABLE=false"
        ) else (
            echo [OK] Dependencies installed successfully.
            echo.
        )
    )
) else (
    echo [INFO] Skipping dependencies (Node.js not available)...
)

REM Create PID file to track processes
echo. > "%DEMO_DIR%\processes.pid"

echo [INFO] Starting system...
echo.

REM Start the Node.js backend server
if "%NODEJS_AVAILABLE%"=="true" (
    echo [1/4] Starting backend server...
    start "Backend Server" /D "%DEMO_DIR%" node server.js
    echo Backend Server PID: %ERRORLEVEL% >> "%DEMO_DIR%\processes.pid"
    echo [OK] Backend Server started
    timeout /t 3 /nobreak >nul
) else (
    echo [1/4] Backend server skipped (Node.js not available)...
)

REM DDS Publishers are started manually via separate scripts
echo [2/4] DDS Publishers will be started manually...
echo Use the following commands for DDS Publishers:
echo - CoreData Publisher: %PROJECT_ROOT%\IDL\CoreData_idl_generated\build\CoreDatamain.exe publisher
echo - Intelligence Publisher: %PROJECT_ROOT%\IDL\Intelligence_idl_generated\build\Intelligencemain.exe publisher
echo - Messaging Publisher: %PROJECT_ROOT%\IDL\Messaging_idl_generated\build\Messagingmain.exe publisher
echo - Monitor: %PROJECT_ROOT%\monitoring\run_monitoring\run_monitoring.bat
echo.

echo.
echo [OK] Demo frontend started!
echo.
echo System status checks:
if "%NODEJS_AVAILABLE%"=="true" (
    echo - Backend Server: http://localhost:3000
    echo - WebSocket Connection: ws://localhost:3000
    echo - DDS Monitor: Will be started manually
)
echo - DDS Publishers: Will be started manually
echo.

REM Wait a bit more for all services to start
if "%NODEJS_AVAILABLE%"=="true" (
    echo [INFO] Opening web browser...
    timeout /t 3 /nobreak >nul
    
    REM Open the web browser
    start http://localhost:3000
) else (
    echo [WARNING] Web dashboard unavailable (Node.js not available)
    echo Only DDS Publishers are running.
)

echo.
echo ========================================
echo    SYSTEM ACTIVE
echo ========================================
echo.
echo Website opened in your browser.
echo To see DDS data, start monitor and publishers manually.
echo DO NOT CLOSE this window while demo is running!
echo.
echo Demo closed.

REM Cleanup section
echo.
echo [INFO] Shutting down system...
echo.

REM Kill all processes from PID file
if exist "%DEMO_DIR%\processes.pid" (
    echo [1/2] Closing demo processes...
    for /f "tokens=2" %%p in ('findstr /R "PID:" "%DEMO_DIR%\processes.pid"') do (
        taskkill /PID %%p /F >nul 2>&1
        if not errorlevel 1 (
            echo [OK] Process %%p closed
        )
    )
)

echo [2/2] Closing Node.js processes...
taskkill /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq Backend Server*" /F >nul 2>&1
taskkill /FI "IMAGENAME eq node.exe" /FI "COMMANDLINE eq *server.js*" /F >nul 2>&1

REM Clean up PID file
if exist "%DEMO_DIR%\processes.pid" (
    del "%DEMO_DIR%\processes.pid"
)

REM Kill any remaining Node.js processes on port 3000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Closed process on port 3000 (PID: %%a)
    )
)

echo.
echo [OK] Demo closed.
echo DDS Publishers and Monitor may still be running.
echo You may need to close them manually.
echo.
if "%NODEJS_AVAILABLE%"=="false" (
    echo Note: Node.js installation required for web dashboard.
    echo Download from: https://nodejs.org/
)
echo.
timeout /t 3 /nobreak >nul
exit /b 0

