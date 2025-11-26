@echo off
setlocal enabledelayedexpansion

REM Always run from this script's directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "MONITORING_DIR=%SCRIPT_DIR%\.."
cd /d "%MONITORING_DIR%"

set "BUILD_BIN=%MONITORING_DIR%\build\monitor.exe"

echo [run_monitoring.bat] Building monitor (if needed)...

REM Check if monitor.exe exists
if not exist "%BUILD_BIN%" (
    echo [run_monitoring.bat] monitor.exe not found, running build_monitoring.bat...
    call "%MONITORING_DIR%\build_monitoring\build_monitoring.bat"
    if errorlevel 1 (
        echo [run_monitoring.bat] ERROR: Build failed.
        exit /b 1
    )
) else (
    REM Try a fast rebuild to ensure it's up to date
    echo [run_monitoring.bat] monitor.exe found, checking if rebuild is needed...
    call "%MONITORING_DIR%\build_monitoring\build_monitoring.bat" >nul 2>&1
)

REM Verify monitor.exe exists after build attempt
if not exist "%BUILD_BIN%" (
    echo [run_monitoring.bat] ERROR: build\monitor.exe not found.
    exit /b 1
)

echo [run_monitoring.bat] Running: %BUILD_BIN%

REM Pass MONITOR_DOMAINS as CLI arg if set
if not "%MONITOR_DOMAINS%"=="" (
    echo [run_monitoring.bat] MONITOR_DOMAINS=%MONITOR_DOMAINS%
    "%BUILD_BIN%" %MONITOR_DOMAINS%
) else (
    "%BUILD_BIN%"
)

set "EXIT_CODE=%ERRORLEVEL%"
exit /b %EXIT_CODE%

