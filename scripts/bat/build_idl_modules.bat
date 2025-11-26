@echo off
REM Fast DDS Project - Simplified Build Script

setlocal enabledelayedexpansion

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

echo DDS Simple Build - Only builds in existing _idl_generated directories

REM Find all _idl_generated directories
set "DIR_COUNT=0"
for /d %%d in ("%IDL_DIR%\*_idl_generated") do (
    set /a DIR_COUNT+=1
    set "GEN_DIR_!DIR_COUNT!=%%d"
)

if %DIR_COUNT%==0 (
    echo No _idl_generated directories found!
    exit /b 1
)

for /l %%i in (1,1,%DIR_COUNT%) do (
    call set "d=%%GEN_DIR_%%i%%"
    for %%f in ("!d!") do (
        set "mod=%%~nf"
        set "mod=!mod:_idl_generated=!"
        echo [INFO] Building: !mod! (!d!)
        cd /d "!d!"
        if exist "CMakeLists.txt" (
            if not exist "build" mkdir "build"
            cd "build"
            REM Clean CMake cache (for portability)
            if exist "CMakeCache.txt" (
                echo [INFO] Cleaning CMake cache (for portability)...
                del /f /q CMakeCache.txt 2>nul
                if exist "CMakeFiles" rmdir /s /q "CMakeFiles" 2>nul
            )
            cmake ..
            if not errorlevel 1 (
                cmake --build . --config Release
                if not errorlevel 1 (
                    echo [OK] Build complete: !d!\build
                    echo Found executables:
                    for %%e in (*.exe) do (
                        echo   - !d!\build\%%e
                    )
                )
            )
            cd ..
        ) else (
            echo CMakeLists.txt not found, skipping: !d!
        )
        cd /d "%PROJECT_ROOT%"
    )
)

echo.
echo All build operations completed. Outputs are in respective _idl_generated\build directories.
echo.
exit /b 0

