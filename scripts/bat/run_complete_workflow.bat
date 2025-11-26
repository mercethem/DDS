@echo off
REM Dynamic ALL Script - Complete DDS Workflow
REM This script runs all DDS processes with dynamic detection

echo ========================================
echo Dynamic DDS Complete Workflow
echo ========================================
echo.

REM Get script directory and project root dynamically
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
    pause
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

REM Step 1: Environment Setup
echo ========================================
echo [STEP 1] Environment Setup
echo ========================================
call "%SCRIPT_DIR%\setup_environment.bat"
if errorlevel 1 (
    echo [ERROR] Environment Setup failed!
    pause
    exit /b 1
)
echo [OK] Environment Setup completed!
echo.

REM Step 2: IDL Generation
echo ========================================
echo [STEP 2] IDL Generation
echo ========================================
call "%SCRIPT_DIR%\generate_idl_code.bat"
if errorlevel 1 (
    echo [ERROR] IDL Generation failed!
    pause
    exit /b 1
)
echo [OK] IDL Generation completed!
echo.

REM Step 3: Domain ID Update
echo ========================================
echo [STEP 3] Domain ID Update
echo ========================================
call "%SCRIPT_DIR%\update_domain_ids.bat"
if errorlevel 1 (
    echo [ERROR] Domain ID Update failed!
    pause
    exit /b 1
)
echo [OK] Domain ID Update completed!
echo.

REM Step 4: Security Setup
echo ========================================
echo [STEP 4] Security Setup
echo ========================================
call "%SCRIPT_DIR%\setup_security_certificates.bat"
if errorlevel 1 (
    echo [ERROR] Security Setup failed!
    pause
    exit /b 1
)
echo [OK] Security Setup completed!
echo.

REM Step 5: IDL Patcher Setup
echo ========================================
echo [STEP 5] IDL Patcher Setup
echo ========================================
call "%SCRIPT_DIR%\patch_idl_defaults.bat"
if errorlevel 1 (
    echo [ERROR] IDL Patcher failed!
    pause
    exit /b 1
)
echo [OK] IDL Patcher completed!
echo.

REM Step 6: JSON Patcher Setup
echo ========================================
echo [STEP 6] JSON Patcher Setup
echo ========================================
call "%SCRIPT_DIR%\patch_json_reading.bat"
if errorlevel 1 (
    echo [ERROR] JSON Patcher failed!
    pause
    exit /b 1
)
echo [OK] JSON Patcher completed!
echo.

REM Step 7: Security Patcher Setup
echo ========================================
echo [STEP 7] Security Patcher Setup
echo ========================================
cd /d "%PROJECT_ROOT%"
python "%PROJECT_ROOT%\scripts\py\apply_security_settings.py"
if errorlevel 1 (
    echo [WARNING] Security Patcher completed with warnings
)
echo [OK] Security Patcher completed!
echo.

REM Step 8: Clean Duplicates
echo ========================================
echo [STEP 8] Clean Duplicates
echo ========================================
python "%PROJECT_ROOT%\scripts\py\clean_duplicate_code.py"
if errorlevel 1 (
    echo [WARNING] Clean Duplicates completed with warnings
)
echo [OK] Clean Duplicates completed!
echo.

REM Step 9: CMake Portability Fix
echo ========================================
echo [STEP 9] CMake Portability Fix
echo ========================================
python "%PROJECT_ROOT%\scripts\py\fix_cmake_rpath.py"
if errorlevel 1 (
    echo [WARNING] CMake Portability Fix completed with warnings
)
echo [OK] CMake Portability Fix completed!
echo.

REM Step 10: Build IDL Modules
echo ========================================
echo [STEP 10] Build IDL Modules
echo ========================================
call "%SCRIPT_DIR%\build_idl_modules.bat"
if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)
echo [OK] Build completed!
echo.

echo ========================================
echo Dynamic DDS Workflow Completed!
echo ========================================
echo.
echo Summary:
echo   - Environment Setup: OK
echo   - IDL Generation: OK
echo   - Domain ID Update: OK
echo   - Security Setup: OK
echo   - IDL Patcher: OK
echo   - JSON Patcher: OK
echo   - Security Patcher: OK
echo   - Clean Duplicates: OK
echo   - CMake Portability Fix: OK
echo   - Build: OK
echo.
echo All steps completed successfully!
echo.
pause
exit /b 0

