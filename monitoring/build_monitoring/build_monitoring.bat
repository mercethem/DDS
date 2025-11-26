@echo off
setlocal enabledelayedexpansion

REM Resolve script and build directories
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "MONITORING_DIR=%SCRIPT_DIR%\.."
set "BUILD_DIR=%MONITORING_DIR%\build"

echo [build_monitoring.bat] Script dir: %SCRIPT_DIR%
echo [build_monitoring.bat] Monitoring dir: %MONITORING_DIR%
echo [build_monitoring.bat] Build dir:  %BUILD_DIR%

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

REM Ensure CMake is available
where cmake >nul 2>&1
if errorlevel 1 (
    echo [build_monitoring.bat] ERROR: cmake not found. Install cmake and retry.
    exit /b 1
)

REM Try to help CMake find Fast-DDS and Fast-CDR
REM Common install locations on Windows: C:\Program Files, C:\Program Files (x86), C:\fastdds
set "CPPATH=%CMAKE_PREFIX_PATH%"
set "PREFIX_FOUND=0"

REM Check common Windows installation paths
if exist "C:\Program Files\fastdds" (
    if "!CPPATH!"=="" (
        set "CPPATH=C:\Program Files\fastdds"
    ) else (
        set "CPPATH=!CPPATH!;C:\Program Files\fastdds"
    )
    set "PREFIX_FOUND=1"
)

if exist "C:\Program Files (x86)\fastdds" (
    if "!CPPATH!"=="" (
        set "CPPATH=C:\Program Files (x86)\fastdds"
    ) else (
        set "CPPATH=!CPPATH!;C:\Program Files (x86)\fastdds"
    )
    set "PREFIX_FOUND=1"
)

if exist "C:\fastdds" (
    if "!CPPATH!"=="" (
        set "CPPATH=C:\fastdds"
    ) else (
        set "CPPATH=!CPPATH!;C:\fastdds"
    )
    set "PREFIX_FOUND=1"
)

if exist "C:\vcpkg\installed\x64-windows" (
    if "!CPPATH!"=="" (
        set "CPPATH=C:\vcpkg\installed\x64-windows"
    ) else (
        set "CPPATH=!CPPATH!;C:\vcpkg\installed\x64-windows"
    )
    set "PREFIX_FOUND=1"
)

REM Set CMAKE_PREFIX_PATH if we found any
if !PREFIX_FOUND!==1 (
    set "CMAKE_PREFIX_PATH=!CPPATH!"
    echo [monitor/build_monitoring] CMAKE_PREFIX_PATH=!CMAKE_PREFIX_PATH!
) else (
    echo [monitor/build_monitoring] CMAKE_PREFIX_PATH not set (using default CMake search paths)
)

REM Configure
echo [monitor/build_monitoring] Configuring with CMake...
cmake -S "%MONITORING_DIR%" -B "%BUILD_DIR%" -DCMAKE_BUILD_TYPE=Release
if errorlevel 1 (
    echo [monitor/build_monitoring] ERROR: CMake configuration failed.
    exit /b 1
)

REM Build with available cores
REM Get number of CPU cores on Windows
for /f "tokens=2 delims==" %%i in ('wmic cpu get NumberOfCores /value ^| findstr "="') do set "JOBS=%%i"
if "!JOBS!"=="" set "JOBS=4"

echo [monitor/build_monitoring] Building with -j!JOBS!...
cmake --build "%BUILD_DIR%" --config Release --parallel !JOBS!
if errorlevel 1 (
    echo [monitor/build_monitoring] ERROR: Build failed.
    exit /b 1
)

REM Check if monitor.exe was built
if exist "%BUILD_DIR%\Release\monitor.exe" (
    echo [monitor/build_monitoring] Built monitor at: %BUILD_DIR%\Release\monitor.exe
    REM Copy to build root for consistency with Linux version
    copy "%BUILD_DIR%\Release\monitor.exe" "%BUILD_DIR%\monitor.exe" >nul 2>&1
) else if exist "%BUILD_DIR%\monitor.exe" (
    echo [monitor/build_monitoring] Built monitor at: %BUILD_DIR%\monitor.exe
) else (
    echo [monitor/build_monitoring] ERROR: build finished but monitor.exe not found.
    exit /b 2
)

echo [monitor/build_monitoring] Build completed successfully!
exit /b 0

