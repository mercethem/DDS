@echo off
REM Clean Linux-specific build artifacts from IDL directories
REM This prepares the project for Windows builds

echo ========================================
echo IDL Linux Artifacts Cleaner
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

cd /d "%PROJECT_ROOT%"

set "IDL_DIR=%CD%\IDL"

if not exist "%IDL_DIR%" (
    echo [ERROR] IDL directory not found!
    exit /b 1
)

echo [INFO] Cleaning Linux build artifacts from IDL directories...
echo.

REM Find all *_idl_generated directories
for /d %%d in ("%IDL_DIR%\*_idl_generated") do (
    echo [CLEAN] Processing: %%~nd
    
    REM Remove Linux-specific files
    if exist "%%d\build" (
        del /f /q /s "%%d\build\*.o" 2>nul
        del /f /q /s "%%d\build\*.a" 2>nul
        del /f /q /s "%%d\build\*.so" 2>nul
        del /f /q /s "%%d\build\CMakeCache.txt" 2>nul
        if exist "%%d\build\CMakeFiles" rmdir /s /q "%%d\build\CMakeFiles" 2>nul
    )
    
    REM Remove Linux build directories
    if exist "%%d\build" rmdir /s /q "%%d\build" 2>nul
    
    echo   - Removed Linux artifacts
)

echo.
echo [OK] Linux artifacts cleanup completed!
echo.
echo Next steps for Windows:
echo 1. Copy project to Windows system
echo 2. Run: %PROJECT_ROOT%\scripts\bat\run_complete_workflow.bat
echo 3. This will regenerate all IDL files for Windows
echo.
pause
exit /b 0

