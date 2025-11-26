@echo off
echo Starting dynamic domain ID update...

REM Get script directory and project root dynamically
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PROJECT_ROOT=%SCRIPT_DIR%\.."
set "IDL_DIR=%PROJECT_ROOT%\IDL"

REM Navigate to IDL directory
cd /d "%IDL_DIR%"

REM Process each IDL file
for %%f in (*.idl) do (
    if exist "%%f" (
        REM Read the first line to check for domain comment
        setlocal enabledelayedexpansion
        set "first_line="
        set /p "first_line=<%%f"
        
        REM Extract domain ID from comment (format: //domain=123)
        echo !first_line! | findstr /R "^//domain=[0-9][0-9]*" >nul
        if not errorlevel 1 (
            for /f "tokens=2 delims==" %%a in ("!first_line!") do set "domain_id=%%a"
            set "domain_id=!domain_id: =!"
            
            for %%b in ("%%f") do (
                set "base_name=%%~nb"
                set "generated_folder=!base_name!_idl_generated"
                set "main_file=!generated_folder!\!base_name!main.cxx"
            )
            
            if exist "!main_file!" (
                echo Updating !main_file! with domain_id = !domain_id!
                REM Use PowerShell to replace the domain_id line
                powershell -Command "(Get-Content '!main_file!') -replace 'int domain_id = [0-9]+;', 'int domain_id = !domain_id!;' | Set-Content '!main_file!'"
            ) else (
                echo Warning: !main_file! not found
            )
        ) else (
            echo Warning: No domain found in %%f
        )
        endlocal
    )
)

echo Dynamic domain ID update complete.
exit /b 0

