@echo off
REM DDS Project Post-Install Build Script for Windows
REM This script runs after system dependencies are installed
REM It handles monitoring application build

setlocal enabledelayedexpansion

REM Get script directory and project root dynamically
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "INIT_DIR=%SCRIPT_DIR%\.."
set "PROJECT_ROOT=%INIT_DIR%\.."

REM Walk up to find project root (contains IDL and scenarios)
set "CURRENT_DIR=%INIT_DIR%"
:find_root
if exist "%CURRENT_DIR%\IDL" if exist "%CURRENT_DIR%\scenarios" (
    set "PROJECT_ROOT=%CURRENT_DIR%"
    goto :found_root
)
set "PARENT_DIR=%CURRENT_DIR%\.."
if "%PARENT_DIR%"=="%CURRENT_DIR%" goto :found_root
set "CURRENT_DIR=%PARENT_DIR%"
goto :find_root
:found_root

REM Clean monitoring build directory and rebuild
echo ========================================
echo Cleaning and Building Monitoring Application...
echo ========================================
echo.

set "MONITORING_BUILD_DIR=%PROJECT_ROOT%\monitoring\build"
set "MONITORING_BUILD_SCRIPT=%PROJECT_ROOT%\monitoring\build_monitoring\build_monitoring.bat"

if exist "%MONITORING_BUILD_DIR%" (
    echo [INFO] Removing existing monitoring build directory...
    rmdir /s /q "%MONITORING_BUILD_DIR%" 2>nul
    if errorlevel 1 (
        echo [WARNING] Failed to remove monitoring build directory
    ) else (
        echo [INFO] Monitoring build directory removed.
    )
) else (
    echo [INFO] No existing monitoring build directory found.
)

if exist "%MONITORING_BUILD_SCRIPT%" (
    echo [INFO] Running build_monitoring.bat...
    call "%MONITORING_BUILD_SCRIPT%"
    if errorlevel 1 (
        echo [ERROR] build_monitoring.bat failed
        exit /b 1
    )
) else (
    echo [WARNING] build_monitoring.bat not found at %MONITORING_BUILD_SCRIPT%
)

echo.
exit /b 0

