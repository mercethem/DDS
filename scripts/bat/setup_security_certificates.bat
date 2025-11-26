@echo off
echo ========================================
echo DDS Security Complete Setup - Dynamic Version
echo ========================================
echo.

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

REM Portability check
echo [INFO] Running portability checks...

REM Check required folders
if not exist "%PROJECT_ROOT%\IDL" (
    echo [ERROR] IDL folder not found!
    echo Project root: %PROJECT_ROOT%
    exit /b 1
)

if not exist "%PROJECT_ROOT%\secure_dds" (
    echo [WARN] Secure DDS folder not found, creating...
    mkdir "%PROJECT_ROOT%\secure_dds\CA" 2>nul
    mkdir "%PROJECT_ROOT%\secure_dds\participants" 2>nul
)

if not exist "%PROJECT_ROOT%\docs" (
    echo [WARN] Docs folder not found, creating...
    mkdir "%PROJECT_ROOT%\docs" 2>nul
)

echo [OK] Project structure is portable
echo.

REM Find Python dynamically
echo [INFO] Searching for Python installation...
call "%SCRIPT_DIR%\find_tools.bat"
if errorlevel 1 (
    echo [ERROR] Python not found!
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

echo This script fully configures DDS Security:
echo 1. Generates certificates
echo 2. Applies security settings
echo 3. Prepares the system
echo.
echo ========================================
echo [STEP 1] Certificate Generation
echo ========================================

REM Check if generate_security_certificates.py exists
if not exist "%PROJECT_ROOT%\scripts\py\generate_security_certificates.py" (
    echo [ERROR] generate_security_certificates.py not found!
    echo Please make sure the file exists in the scripts\py folder.
    exit /b 1
)

REM Run certificate generation
echo [INFO] Generating DDS Security certificates...
cd "%PROJECT_ROOT%\scripts\py"
%PYTHON_CMD% "%PROJECT_ROOT%\scripts\py\generate_security_certificates.py"
set CERT_EXIT_CODE=%ERRORLEVEL%

if %CERT_EXIT_CODE%==0 (
    echo [OK] Certificate generation completed successfully!
) else (
    echo [ERROR] Certificate generation failed with exit code %CERT_EXIT_CODE%!
    exit /b 1
)

echo.
echo ========================================
echo [STEP 2] Security Configuration
echo ========================================

REM Check if apply_security_settings.py exists
if not exist "%PROJECT_ROOT%\scripts\py\apply_security_settings.py" (
    echo [ERROR] apply_security_settings.py not found!
    echo Please make sure the file exists in the scripts\py folder.
    exit /b 1
)

REM Run security configuration
echo [INFO] Applying DDS Security configuration...
cd "%PROJECT_ROOT%\scripts\py"
%PYTHON_CMD% "%PROJECT_ROOT%\scripts\py\apply_security_settings.py"
set SEC_EXIT_CODE=%ERRORLEVEL%

if %SEC_EXIT_CODE%==0 (
    echo [OK] Security configuration completed successfully!
) else (
    echo [ERROR] Security configuration failed with exit code %SEC_EXIT_CODE%!
    exit /b 1
)

echo.
echo ========================================
echo DDS Security Setup Completed!
echo ========================================
echo.
echo Summary:
echo   - Certificate Generation: OK
echo   - Security Configuration: OK
echo   - System is ready for secure DDS communication
echo.
echo Your DDS system now has security enabled!
exit /b 0

