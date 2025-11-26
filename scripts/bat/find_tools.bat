@echo off
REM Dynamic Finder - Windows Version
REM Cross-platform tool detection for DDS project

echo === Dynamic Environment Finder - Windows Version ===
echo Detecting Python, Java, and CMake installations...

REM Initialize variables
set "PYTHON_PATH="
set "JAVA_PATH="
set "CMAKE_PATH="

REM Python Detection
echo.
echo [INFO] Searching for Python installations...

REM Check system Python
where python >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('where python') do set "PYTHON_PATH=%%i"
    echo [OK] System Python found: %PYTHON_PATH%
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%i in ('where py') do set "PYTHON_PATH=%%i"
        echo [OK] Python Launcher found: %PYTHON_PATH%
    )
)

REM Check common Python installation paths
if "%PYTHON_PATH%"=="" (
    if exist "C:\Python3\python.exe" (
        set "PYTHON_PATH=C:\Python3\python.exe"
        echo [OK] Python found: %PYTHON_PATH%
    ) else if exist "C:\Python39\python.exe" (
        set "PYTHON_PATH=C:\Python39\python.exe"
        echo [OK] Python found: %PYTHON_PATH%
    ) else if exist "C:\Python310\python.exe" (
        set "PYTHON_PATH=C:\Python310\python.exe"
        echo [OK] Python found: %PYTHON_PATH%
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python3*\python.exe" (
        for %%p in ("%LOCALAPPDATA%\Programs\Python\Python3*\python.exe") do (
            set "PYTHON_PATH=%%p"
            echo [OK] Python found: %PYTHON_PATH%
            goto :python_found
        )
    )
    :python_found
)

if "%PYTHON_PATH%"=="" (
    echo [ERROR] Python not found!
) else (
    echo [SUCCESS] Using Python: %PYTHON_PATH%
)

REM Java Detection
echo.
echo [INFO] Searching for Java installations...

where java >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('where java') do set "JAVA_PATH=%%i"
    echo [OK] System Java found: %JAVA_PATH%
)

REM Check common Java installation paths
if "%JAVA_PATH%"=="" (
    if exist "C:\Program Files\Java\jdk-*\bin\java.exe" (
        for %%j in ("C:\Program Files\Java\jdk-*\bin\java.exe") do (
            set "JAVA_PATH=%%j"
            echo [OK] Java found: %JAVA_PATH%
            goto :java_found
        )
    ) else if exist "C:\Program Files (x86)\Java\jdk-*\bin\java.exe" (
        for %%j in ("C:\Program Files (x86)\Java\jdk-*\bin\java.exe") do (
            set "JAVA_PATH=%%j"
            echo [OK] Java found: %JAVA_PATH%
            goto :java_found
        )
    )
    :java_found
)

if "%JAVA_PATH%"=="" (
    echo [ERROR] Java not found!
) else (
    echo [SUCCESS] Using Java: %JAVA_PATH%
)

REM CMake Detection
echo.
echo [INFO] Searching for CMake installations...

where cmake >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('where cmake') do set "CMAKE_PATH=%%i"
    echo [OK] System CMake found: %CMAKE_PATH%
)

REM Check common CMake installation paths
if "%CMAKE_PATH%"=="" (
    if exist "C:\Program Files\CMake\bin\cmake.exe" (
        set "CMAKE_PATH=C:\Program Files\CMake\bin\cmake.exe"
        echo [OK] CMake found: %CMAKE_PATH%
    ) else if exist "C:\Program Files (x86)\CMake\bin\cmake.exe" (
        set "CMAKE_PATH=C:\Program Files (x86)\CMake\bin\cmake.exe"
        echo [OK] CMake found: %CMAKE_PATH%
    )
)

if "%CMAKE_PATH%"=="" (
    echo [ERROR] CMake not found!
) else (
    echo [SUCCESS] Using CMake: %CMAKE_PATH%
)

REM Export environment variables
set "DDS_PYTHON_PATH=%PYTHON_PATH%"
set "DDS_JAVA_PATH=%JAVA_PATH%"
set "DDS_CMAKE_PATH=%CMAKE_PATH%"

REM Create environment file for other scripts
set "ENV_FILE=%~dp0export_environment_vars.bat"
(
    echo @echo off
    echo REM DDS Environment Variables - Auto-generated
    echo set "DDS_PYTHON_PATH=%PYTHON_PATH%"
    echo set "DDS_JAVA_PATH=%JAVA_PATH%"
    echo set "DDS_CMAKE_PATH=%CMAKE_PATH%"
) > "%ENV_FILE%"

echo.
echo === Environment Setup Complete ===
echo Environment variables exported and saved to: %ENV_FILE%

REM Executable Detection
echo.
echo [INFO] Searching for DDS executables...

REM Find IDL generated executables
REM Get script directory and project root dynamically
set "SCRIPT_DIR_TEMP=%~dp0"
set "SCRIPT_DIR_TEMP=%SCRIPT_DIR_TEMP:~0,-1%"
set "PROJECT_ROOT_TEMP=%SCRIPT_DIR_TEMP%\.."

REM Walk up to find project root (contains IDL and scenarios)
set "CURRENT_DIR=%SCRIPT_DIR_TEMP%"
:find_root_temp
if exist "%CURRENT_DIR%\IDL" if exist "%CURRENT_DIR%\scenarios" (
    set "PROJECT_ROOT_TEMP=%CURRENT_DIR%"
    goto :root_found_temp
)
if "%CURRENT_DIR%"=="%CURRENT_DIR:\..=%" goto :root_found_temp
set "CURRENT_DIR=%CURRENT_DIR%\.."
goto :find_root_temp
:root_found_temp

set "IDL_DIR=%PROJECT_ROOT_TEMP%\IDL"
if exist "%IDL_DIR%" (
    echo Scanning IDL directory: %IDL_DIR%
    
    for /d %%d in ("%IDL_DIR%\*_idl_generated") do (
        REM Check Release directory
        if exist "%%d\Release" (
            for %%e in ("%%d\Release\*.exe") do (
                echo [FOUND] %%e
            )
        )
        
        REM Check Debug directory
        if exist "%%d\Debug" (
            for %%e in ("%%d\Debug\*.exe") do (
                echo [FOUND] %%e
            )
        )
        
        REM Check build directory
        if exist "%%d\build" (
            for %%e in ("%%d\build\*.exe") do (
                echo [FOUND] %%e
            )
        )
    )
) else (
    echo [WARNING] IDL directory not found: %IDL_DIR%
)

echo.
echo Dynamic finder completed successfully!
exit /b 0

