@echo off
setlocal enabledelayedexpansion

REM Always run from this script's directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "DEMO_DIR=%SCRIPT_DIR%\.."
cd /d "%DEMO_DIR%"

echo ========================================
echo    DEMO BUILD_DEMO SCRIPT
echo    Node.js Dependencies Installer
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Please install Node.js to continue.
    echo.
    echo Installation instructions:
    echo   Download from: https://nodejs.org/
    echo   Or use Chocolatey: choco install nodejs
    echo.
    pause
    exit /b 1
)

REM Check if npm is installed
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found!
    echo Please install npm to continue.
    echo.
    echo Installation instructions:
    echo   Download Node.js from: https://nodejs.org/ (includes npm)
    echo.
    pause
    exit /b 1
)

REM Display versions
for /f "delims=" %%i in ('node --version') do set "NODE_VERSION=%%i"
for /f "delims=" %%i in ('npm --version') do set "NPM_VERSION=%%i"
echo [OK] Node.js version: %NODE_VERSION%
echo [OK] npm version: %NPM_VERSION%
echo.

REM Check if package.json exists
if not exist "%DEMO_DIR%\package.json" (
    echo [ERROR] package.json not found in %DEMO_DIR%
    pause
    exit /b 1
)

echo [STEP] Installing Node.js dependencies...
echo.

REM Install dependencies
call npm install

if errorlevel 1 (
    echo [ERROR] Dependency installation failed!
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed successfully!
echo.

REM Verify node_modules directory
if exist "%DEMO_DIR%\node_modules" (
    echo [OK] node_modules directory created
) else (
    echo [WARNING] node_modules directory not found after installation
)

echo.
echo ========================================
echo    BUILD_DEMO COMPLETED
echo ========================================
echo.
echo Demo is ready to run!
echo.
echo To start the demo:
echo   Windows: run_demo\run_demo.bat
echo   Linux:   ./run_demo/run_demo.sh
echo.
echo Or manually:
echo   npm start
echo.

pause
exit /b 0

