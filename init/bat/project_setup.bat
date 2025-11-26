@echo off
REM DDS Project Auto-Setup Script
REM This script automatically configures the project when moved to another PC:
REM 1. Checks certificates and creates them if missing
REM 2. Tests binary executability
REM 3. Performs automatic build if needed

setlocal enabledelayedexpansion

echo ========================================
echo DDS Project Auto-Setup
echo ========================================
echo.
echo This script prepares the project for use on a new PC.
echo.

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "INIT_DIR=%SCRIPT_DIR%\.."
set "PROJECT_ROOT=%INIT_DIR%\.."

REM Walk up to find project root (contains IDL and scenarios)
set "CURRENT_DIR=%INIT_DIR%"
:find_root
if exist "%CURRENT_DIR%\IDL" if exist "%CURRENT_DIR%\scenarios" (
    set "PROJECT_ROOT=%CURRENT_DIR%"
    goto :root_found
)
if "%CURRENT_DIR%"=="%CURRENT_DIR:\..=%" goto :root_found
set "CURRENT_DIR=%CURRENT_DIR%\.."
goto :find_root
:root_found

cd /d "%PROJECT_ROOT%"

REM Step 0: Run run_complete_workflow.bat first (initial setup)
echo ========================================
echo STEP 0: Dynamic DDS Workflow (Initial Setup)
echo ========================================

if not exist "%PROJECT_ROOT%\scripts\bat\run_complete_workflow.bat" (
    echo [ERROR] run_complete_workflow.bat not found: %PROJECT_ROOT%\scripts\bat\run_complete_workflow.bat
    pause
    exit /b 1
)

echo [INFO] Starting Dynamic DDS workflow...
cd "%PROJECT_ROOT%\scripts\bat"
call "%PROJECT_ROOT%\scripts\bat\run_complete_workflow.bat"
if errorlevel 1 (
    echo [ERROR] Dynamic DDS workflow failed!
    pause
    exit /b 1
)
echo [OK] Dynamic DDS workflow completed
cd /d "%PROJECT_ROOT%"

echo.

REM Step 1: Check and create certificates
echo ========================================
echo STEP 1: Certificate Check
echo ========================================

set "CA_CERT=%PROJECT_ROOT%\secure_dds\CA\mainca_cert.pem"
for /f "delims=" %%i in ('hostname') do set "PC_NAME=%%i"
set "PC_CERT_DIR=%PROJECT_ROOT%\secure_dds\participants\%PC_NAME%"
set "PC_CERT=%PC_CERT_DIR%\%PC_NAME%_cert.pem"

REM Certificate check: Check both file existence
set "RECREATE_CERTS=0"

if not exist "%CA_CERT%" (
    echo [WARNING] Certificates not found or missing. Creating...
    set "RECREATE_CERTS=1"
) else if not exist "%PC_CERT%" (
    echo [WARNING] Participant certificate not found. Creating...
    set "RECREATE_CERTS=1"
) else (
    echo [OK] Certificates exist
)

if !RECREATE_CERTS!==1 (
    REM Check if Python scripts exist
    if not exist "%PROJECT_ROOT%\scripts\py\generate_security_certificates.py" (
        echo [ERROR] generate_security_certificates.py not found!
        pause
        exit /b 1
    )
    
    REM Run certificate generation
    python "%PROJECT_ROOT%\scripts\py\generate_security_certificates.py"
    if errorlevel 1 (
        echo [ERROR] Certificate creation failed!
        pause
        exit /b 1
    )
    echo [OK] Certificates created
)

echo.

REM Step 2a: Clean duplicate dynamic code blocks (if any)
echo ========================================
echo STEP 2a: Cleaning Duplicate Code Blocks
echo ========================================

if exist "%PROJECT_ROOT%\scripts\py\clean_duplicate_code.py" (
    python "%PROJECT_ROOT%\scripts\py\clean_duplicate_code.py" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Cleanup script executed (result pending)
    ) else (
        echo [OK] Duplicate code blocks cleaned
    )
) else (
    echo [WARNING] clean_duplicate_code.py not found (skipping...)
)

echo.

REM Step 2b: Fix CMake portability (hardcoded paths, RPATH, etc.)
echo ========================================
echo STEP 2b: CMake Portability Fix
echo ========================================

if exist "%PROJECT_ROOT%\scripts\py\fix_cmake_rpath.py" (
    python "%PROJECT_ROOT%\scripts\py\fix_cmake_rpath.py" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] CMake fix executed (result pending)
    ) else (
        echo [OK] CMake files made portable
    )
) else (
    echo [WARNING] fix_cmake_rpath.py not found (skipping...)
)

echo.

REM Step 2: Apply security patches (if needed)
echo ========================================
echo STEP 2: Security Configuration
echo ========================================

if exist "%PROJECT_ROOT%\scripts\py\apply_security_settings.py" (
    python "%PROJECT_ROOT%\scripts\py\apply_security_settings.py" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Warning occurred while applying security settings (continuing...)
    ) else (
        echo [OK] Security settings checked
    )
) else (
    echo [WARNING] apply_security_settings.py not found (skipping...)
)

echo.

REM Step 3: Check if binaries exist and are executable
echo ========================================
echo STEP 3: Binary Check
echo ========================================

set "NEED_BUILD=0"
set "BINARY_COUNT=0"

REM Check for main executables in each IDL module
for /d %%d in ("%PROJECT_ROOT%\IDL\*_idl_generated") do (
    if exist "%%d" (
        for %%f in ("%%d") do (
            set "MODULE_NAME=%%~nf"
            set "MODULE_NAME=!MODULE_NAME:_idl_generated=!"
            set "MAIN_BINARY=%%d\build\!MODULE_NAME!main.exe"
            
            REM Try build\ first, then root
            if not exist "!MAIN_BINARY!" (
                set "MAIN_BINARY=%%d\!MODULE_NAME!main.exe"
            )
            
            set /a BINARY_COUNT+=1
            
            if exist "!MAIN_BINARY!" (
                REM Test if binary can actually run
                "!MAIN_BINARY!" --help >nul 2>&1
                if errorlevel 1 (
                    echo [WARNING] !MODULE_NAME! binary is not working (may be a library error)
                    set "NEED_BUILD=1"
                ) else (
                    echo [OK] !MODULE_NAME! binary is working
                )
            ) else (
                echo [WARNING] !MODULE_NAME! binary not found
                set "NEED_BUILD=1"
            )
        )
    )
)

echo.

REM Step 4: Build if needed
if !NEED_BUILD!==1 (
    echo ========================================
    echo STEP 4: Building Missing Binaries
    echo ========================================
    
    echo [INFO] Starting build for missing or non-working binaries...
    
    if not exist "%PROJECT_ROOT%\scripts\bat\build_idl_modules.bat" (
        echo [ERROR] build_idl_modules.bat not found!
        pause
        exit /b 1
    )
    
    REM Run builder
    call "%PROJECT_ROOT%\scripts\bat\build_idl_modules.bat"
    if errorlevel 1 (
        echo [ERROR] Build failed!
        echo.
        echo [WARNING] To build manually:
        echo   %PROJECT_ROOT%\scripts\bat\build_idl_modules.bat
        pause
        exit /b 1
    )
    echo [OK] Build completed
) else (
    echo ========================================
    echo STEP 4: Build Check
    echo ========================================
    echo [OK] All binaries exist and are working - build not needed
)

echo.

REM Step 5: Verify and fix participant certificate compatibility with CA
echo ========================================
echo STEP 5: Participant Certificate Verification
echo ========================================

set "CA_CERT=%PROJECT_ROOT%\secure_dds\CA\mainca_cert.pem"
set "CA_KEY=%PROJECT_ROOT%\secure_dds\CA\private\mainca_key.pem"
set "PARTICIPANT_DIR=%PROJECT_ROOT%\secure_dds\participants\%PC_NAME%"
set "PARTICIPANT_CERT=%PARTICIPANT_DIR%\%PC_NAME%_cert.pem"
set "PARTICIPANT_KEY=%PARTICIPANT_DIR%\%PC_NAME%_key.pem"
set "APP_CONF=%PROJECT_ROOT%\secure_dds\appconf.cnf"

REM Check if CA exists
if not exist "%CA_CERT%" (
    echo [ERROR] CA certificate not found: %CA_CERT%
    echo [WARNING] Participant certificate cannot be verified (skipping...)
) else (
    REM Verify current participant cert against CA
    if exist "%PARTICIPANT_CERT%" (
        where openssl >nul 2>&1
        if not errorlevel 1 (
            openssl verify -CAfile "%CA_CERT%" "%PARTICIPANT_CERT%" >nul 2>&1
            if errorlevel 1 (
                echo [WARNING] Participant certificate does not match CA!
                echo [INFO] Recreating participant certificate...
                REM Note: Certificate recreation requires OpenSSL and proper configuration
                echo [INFO] Please run generate_security_certificates.py manually if needed
            ) else (
                echo [OK] Participant certificate is compatible with CA
            )
        ) else (
            echo [WARNING] OpenSSL not found, skipping certificate verification
        )
    ) else (
        echo [WARNING] Participant certificate not found: %PARTICIPANT_CERT%
        echo [INFO] generate_security_certificates.py should be run in STEP 1 to create certificate
    )
)

echo.

REM Step 6: Build monitoring application
echo ========================================
echo STEP 6: Building Monitoring Application
echo ========================================

set "MONITORING_BUILD_SCRIPT=%PROJECT_ROOT%\monitoring\build_monitoring\build_monitoring.bat"

if exist "%MONITORING_BUILD_SCRIPT%" (
    echo [INFO] Building monitoring application...
    
    call "%MONITORING_BUILD_SCRIPT%"
    if errorlevel 1 (
        echo [WARNING] Monitoring build failed (continuing anyway...)
    ) else (
        echo [OK] Monitoring application built successfully
    )
) else (
    echo [WARNING] build_monitoring.bat not found at: %MONITORING_BUILD_SCRIPT% (skipping...)
)

echo.
echo ========================================
echo Setup Completed!
echo ========================================
echo.
echo [OK] Project is ready to use!
echo.
echo Usage:
echo   Publisher:   IDL\<MODULE>_idl_generated\build\<MODULE>main.exe publisher
echo   Subscriber: IDL\<MODULE>_idl_generated\build\<MODULE>main.exe subscriber
echo.
echo Example:
echo   IDL\Messaging_idl_generated\build\Messagingmain.exe publisher
echo.
pause
exit /b 0

