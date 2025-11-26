@echo off
REM Simple Dynamic Test Script - Windows Version
REM Test all IDL modules dynamically by discovering *_idl_generated dirs

echo ========================================
echo Simple Dynamic Test Script
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

set "IDL_DIR=%PROJECT_ROOT%\IDL"

echo Script directory: %SCRIPT_DIR%
echo Project root: %PROJECT_ROOT%
echo IDL directory: %IDL_DIR%

cd /d "%IDL_DIR%"

echo [INFO] Scanning for *_idl_generated directories...

REM Initialize test variables
set /a TEST_COUNT=0
set /a SUCCESS_COUNT=0

REM Discover and run all *_idl_generated modules
for /d %%d in (*_idl_generated) do (
    set /a TEST_COUNT+=1
    for %%f in ("%%d") do (
        set "module_name=%%~nf"
        set "module_name=!module_name:_idl_generated=!"
        echo [!TEST_COUNT!] Testing !module_name!...
        
        REM Determine working directory (prefer build\ if exists)
        set "work_dir=%IDL_DIR%\!module_name!_idl_generated"
        if exist "!work_dir!\build" (
            set "work_dir=!work_dir!\build"
        )
        
        REM Find an executable containing 'main' in its name
        set "found_exe="
        for %%e in ("!work_dir!\*main*.exe") do (
            if exist "%%e" (
                set "found_exe=%%~nxe"
                goto :exe_found
            )
        )
        :exe_found
        
        if "!found_exe!"=="" (
            echo   No '*main*' executable found in: !work_dir!
            goto :continue_loop
        )
        
        echo   - Starting Publisher...
        start "!module_name! Publisher" cmd /k "cd /d !work_dir! && echo Starting !module_name! Publisher... && echo Executable: !found_exe! publisher && echo ---------------------------------------- && !found_exe! publisher && echo. && echo ---------------------------------------- && echo Process finished. Press Enter to close... && pause"
        timeout /t 2 /nobreak >nul
        
        echo   - Starting Subscriber...
        start "!module_name! Subscriber" cmd /k "cd /d !work_dir! && echo Starting !module_name! Subscriber... && echo Executable: !found_exe! subscriber && echo ---------------------------------------- && !found_exe! subscriber && echo. && echo ---------------------------------------- && echo Process finished. Press Enter to close... && pause"
        echo   [OK] !module_name! test started
        set /a SUCCESS_COUNT+=1
        echo.
        
        :continue_loop
    )
)

echo ========================================
echo Simple Dynamic Test Summary:
echo ========================================
echo Total modules: %TEST_COUNT%
echo Successful: %SUCCESS_COUNT%
echo.

if %SUCCESS_COUNT% GTR 0 (
    echo [OK] Test completed successfully!
) else (
    echo [ERROR] No tests were successful!
    echo.
    echo Check:
    echo   - Are there *_idl_generated folders?
    echo   - Are there 'build' folders with executables?
    echo   - Did the build process complete successfully?
)

echo ========================================
echo.
echo Press Enter to continue...
pause
exit /b 0

