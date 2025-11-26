@echo off

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

REM Check if period argument is provided
if "%~1"=="" (
    echo Starting interactive mode...
    echo You can enter different values for each file.
    echo.
    REM Run in interactive mode (no arguments)
    python "%PROJECT_ROOT%\scripts\py\set_publisher_period.py"
) else (
    set "PERIOD=%~1"
    
    REM Validate that PERIOD is a positive integer
    echo %PERIOD% | findstr /R "^[1-9][0-9]*$" >nul
    if errorlevel 1 (
        echo ERROR: Period must be a positive integer!
        echo Usage: set_publisher_period.bat [period_in_ms]
        echo Example: set_publisher_period.bat 200
        echo          (without argument: interactive mode)
        exit /b 1
    )
    
    echo Running: set_publisher_period.py (period=%PERIOD% ms)...
    echo Note: All files will be updated with the same value.
    echo       Run without argument for interactive mode: set_publisher_period.bat
    echo.
    
    REM Run with period argument (non-interactive mode)
    python "%PROJECT_ROOT%\scripts\py\set_publisher_period.py" %PERIOD%
)

set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE%==0 (
    echo Operation completed successfully.
) else (
    echo An error occurred during operation.
)

exit /b %EXIT_CODE%

