@echo off
REM Dynamic QoS Patcher - Portable QoS Configuration
REM This script runs QoS patcher with dynamic Python detection

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PROJECT_ROOT=%SCRIPT_DIR%\.."

REM Walk up to find project root (contains IDL and scenarios)
set "CURRENT_DIR=%SCRIPT_DIR%"
:find_root
if exist "%CURRENT_DIR%\IDL" if exist "%CURRENT_DIR%\scenarios" (
    set "PROJECT_ROOT=%CURRENT_DIR%"
    goto :root_found
)
if "%CURRENT_DIR%"=="%CURRENT_DIR:\..=%" goto :root_found
set "CURRENT_DIR=%CURRENT_DIR%\.."
goto :find_root
:root_found

cd /d "%SCRIPT_DIR%"

echo ========================================
echo Dynamic QoS Patcher GUI Starting...
echo ========================================
echo.

REM Find Python dynamically
echo [INFO] Searching for Python installation...
call "%SCRIPT_DIR%\find_tools.bat"
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

REM Use python as default
where python >nul 2>&1
if errorlevel 1 (
    set "PYTHON_CMD=py"
) else (
    set "PYTHON_CMD=python"
)
echo [OK] Using Python: %PYTHON_CMD%
echo.

REM Check if QoS patcher GUI exists
if not exist "%PROJECT_ROOT%\scripts\py\qos_settings_patcher_gui.py" (
    echo [ERROR] qos_settings_patcher_gui.py not found!
    echo Please make sure the file exists in the scripts\py folder.
    pause
    exit /b 1
)

REM Run QoS patcher GUI
echo [STEP] Starting QoS Patcher GUI...
cd "%PROJECT_ROOT%\scripts\py"
%PYTHON_CMD% qos_settings_patcher_gui.py
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
echo QoS Patcher GUI finished.
echo ========================================
echo.

if %EXIT_CODE%==0 (
    echo [OK] QoS Patcher completed successfully!
) else (
    echo [ERROR] QoS Patcher failed with exit code %EXIT_CODE%!
)

echo.
pause
exit /b %EXIT_CODE%

