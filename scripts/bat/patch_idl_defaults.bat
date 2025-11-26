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

REM Verify and display the new working directory (Project Root)
echo Project root set to: %CD%
echo.

echo Running: idl_default_data_patcher.py...

REM Run the Python script with absolute path from project root
python "%PROJECT_ROOT%\scripts\py\idl_default_data_patcher.py"
if errorlevel 1 (
    echo Error occurred!
    pause
    exit /b 1
)

echo.
echo Operation completed. Press any key to close...
pause
exit /b 0

