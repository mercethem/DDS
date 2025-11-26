@echo off
REM DDS Project Dependency Installation Script for Windows

echo ========================================
echo DDS Project - Windows Dependencies Installer
echo ========================================
echo.

REM Admin check
net session >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Some operations may require administrator privileges.
    echo Please run as administrator if installation fails.
    echo.
)

REM Check Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo [INFO] Windows version: %VERSION%
echo.

echo [STEP 1/6] Checking for Chocolatey package manager...
where choco >nul 2>&1
if errorlevel 1 (
    echo [INFO] Chocolatey not found. Installing Chocolatey...
    echo Please visit https://chocolatey.org/install for installation instructions.
    echo Or install dependencies manually.
    echo.
    echo [INFO] To install Chocolatey, run PowerShell as Administrator:
    echo   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    echo.
    exit /b 1
) else (
    echo [OK] Chocolatey found
)

echo.
echo [STEP 2/6] Installing basic build tools...
choco install -y cmake git curl wget unzip
if errorlevel 1 (
    echo [ERROR] Failed to install build tools
    exit /b 1
)

echo.
echo [STEP 3/6] Installing Python and Java...
choco install -y python3 openjdk11
if errorlevel 1 (
    echo [ERROR] Failed to install Python or Java
    exit /b 1
)

REM Refresh environment variables
call refreshenv

echo.
echo [STEP 4/6] Installing library dependencies...
echo [INFO] Windows requires manual installation of:
echo   - OpenSSL (download from https://slproweb.com/products/Win32OpenSSL.html)
echo   - Fast-DDS (build from source or use pre-built binaries)
echo   - Boost libraries (via vcpkg or pre-built)
echo.
echo [INFO] For OpenSSL:
echo   1. Download Win64 OpenSSL from https://slproweb.com/products/Win32OpenSSL.html
echo   2. Install to C:\OpenSSL-Win64
echo   3. Add C:\OpenSSL-Win64\bin to PATH
echo.

echo [STEP 5/6] Installing Fast-DDS...
echo [INFO] Fast-DDS installation options:
echo   1. Build from source: https://fast-dds.docs.eprosima.com/en/latest/installation/sources/sources.html
echo   2. Use pre-built binaries (if available)
echo   3. Use vcpkg: vcpkg install fastdds
echo.
echo [WARNING] Fast-DDS must be installed manually on Windows
echo.

echo [STEP 6/6] Setting environment variables...

REM Set JAVA_HOME
for /f "delims=" %%i in ('where java') do (
    set "JAVA_PATH=%%i"
    for %%j in ("%%~dpi.") do set "JAVA_HOME=%%~fj"
    set "JAVA_HOME=!JAVA_HOME:~0,-2!"
)
if not defined JAVA_HOME (
    if exist "C:\Program Files\Java\jdk-11" (
        set "JAVA_HOME=C:\Program Files\Java\jdk-11"
    )
)

REM Add to system environment (requires admin)
echo [INFO] Adding environment variables...
if defined JAVA_HOME (
    setx JAVA_HOME "%JAVA_HOME%" /M >nul 2>&1
    setx PATH "%PATH%;%JAVA_HOME%\bin" /M >nul 2>&1
)

REM Add OpenSSL to PATH if exists
if exist "C:\OpenSSL-Win64\bin" (
    setx PATH "%PATH%;C:\OpenSSL-Win64\bin" /M >nul 2>&1
)

echo.
echo ========================================
echo Installation Completed!
echo ========================================
echo.
echo Next steps:
echo 1. Restart terminal or run: refreshenv
echo 2. Install Fast-DDS manually
echo 3. Install OpenSSL manually
echo 4. Run project: scripts\bat\run_complete_workflow.bat
echo.
echo Note: Some dependencies require manual installation on Windows.
echo See README.md for detailed instructions.
echo.
exit /b 0

