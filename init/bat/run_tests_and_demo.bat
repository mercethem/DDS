@echo off
REM Orchestrator: run test_idl_modules.bat, wait until all modules are up, then start run_demo.bat

setlocal enabledelayedexpansion

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

set "SCRIPTS_BAT=%PROJECT_ROOT%\scripts\bat"
set "IDL_DIR=%PROJECT_ROOT%\IDL"

echo [INFO] Starting test_idl_modules.bat...

REM Run test script in background
start "DDS Test" cmd /c "cd /d %SCRIPTS_BAT% && call test_idl_modules.bat"

REM Build expected process patterns by discovering modules
set "PATTERN_COUNT=0"

for /d %%d in ("%IDL_DIR%\*_idl_generated") do (
    if exist "%%d" (
        for %%f in ("%%d") do (
            set "mod=%%~nf"
            set "mod=!mod:_idl_generated=!"
            set "work_dir=%%d"
            if exist "%%d\build" (
                set "work_dir=%%d\build"
            )
            
            REM Find first *main* executable
            set "exe="
            for %%e in ("!work_dir!\*main*.exe") do (
                if exist "%%e" (
                    set "exe=%%~nxe"
                    goto :exe_found
                )
            )
            :exe_found
            
            if not "!exe!"=="" (
                REM We expect two processes per module: publisher and subscriber
                set /a PATTERN_COUNT+=1
                set "EXPECTED_PATTERN_!PATTERN_COUNT!=!work_dir!\!exe! publisher"
                set /a PATTERN_COUNT+=1
                set "EXPECTED_PATTERN_!PATTERN_COUNT!=!work_dir!\!exe! subscriber"
            )
        )
    )
)

echo [INFO] Waiting up to 20s for modules to start (best-effort)...
set "deadline=20"
set "started_any=0"

for /l %%i in (1,1,20) do (
    for /l %%j in (1,1,!PATTERN_COUNT!) do (
        call set "pat=%%EXPECTED_PATTERN_%%j%%"
        tasklist /FI "IMAGENAME eq !exe!" 2>nul | find /I "!exe!" >nul
        if not errorlevel 1 (
            set "started_any=1"
            goto :found_process
        )
    )
    :found_process
    if !started_any!==1 (
        echo [OK] At least one module detected running.
        goto :start_demo
    )
    timeout /t 1 /nobreak >nul
)

:start_demo
echo [INFO] Launching run_demo.bat...
call "%PROJECT_ROOT%\demo\run_demo\run_demo.bat"
set "exit_code=%ERRORLEVEL%"
echo [INFO] run_demo.bat exited with code: %exit_code%
exit /b %exit_code%

