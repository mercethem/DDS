@echo off
REM Fast DDS IDL Generator - Portable Version

echo ========================================
echo Fast DDS IDL Generator - Portable Version
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

REM Portability check
echo [INFO] Running portability checks...

REM Check required folders
if not exist "%PROJECT_ROOT%\IDL" (
    echo [ERROR] IDL folder not found!
    echo Project root: %PROJECT_ROOT%
    pause
    exit /b 1
)

echo [OK] Project structure is portable
echo.

REM Java check
where java >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Java is not installed!
    pause
    exit /b 1
)

for /f "delims=" %%i in ('where java') do set JAVA_PATH=%%i
echo [OK] Java found: %JAVA_PATH%

REM JSON library check and setup
echo [INFO] Checking JSON library...
set "JSON_INCLUDE_DIR=%PROJECT_ROOT%\include\nlohmann"
set "JSON_HEADER=%JSON_INCLUDE_DIR%\json.hpp"

if not exist "%JSON_HEADER%" (
    echo [INFO] JSON library not found, downloading...
    if not exist "%JSON_INCLUDE_DIR%" mkdir "%JSON_INCLUDE_DIR%"
    
    where curl >nul 2>&1
    if not errorlevel 1 (
        curl -L -o "%JSON_HEADER%" "https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp"
        if errorlevel 1 (
            echo [ERROR] Failed to download JSON library
            pause
            exit /b 1
        )
        echo [OK] JSON library downloaded successfully
    ) else (
        echo [ERROR] curl not found! Cannot download JSON library
        pause
        exit /b 1
    )
) else (
    echo [OK] JSON library found: %JSON_HEADER%
)

REM Find OpenSSL paths dynamically
echo [INFO] Searching for OpenSSL paths...

set "OPENSSL_ROOT_DIR="
set "OPENSSL_LIB_DIR="
set "OPENSSL_INCLUDE_DIR="

REM Check common Windows OpenSSL paths
if exist "C:\OpenSSL-Win64\lib" (
    set "OPENSSL_ROOT_DIR=C:\OpenSSL-Win64"
    set "OPENSSL_LIB_DIR=C:\OpenSSL-Win64\lib"
    set "OPENSSL_INCLUDE_DIR=C:\OpenSSL-Win64\include"
    echo [OK] OpenSSL found: %OPENSSL_ROOT_DIR%
) else if exist "C:\Program Files\OpenSSL-Win64\lib" (
    set "OPENSSL_ROOT_DIR=C:\Program Files\OpenSSL-Win64"
    set "OPENSSL_LIB_DIR=C:\Program Files\OpenSSL-Win64\lib"
    set "OPENSSL_INCLUDE_DIR=C:\Program Files\OpenSSL-Win64\include"
    echo [OK] OpenSSL found: %OPENSSL_ROOT_DIR%
) else (
    echo [WARNING] OpenSSL not found in standard paths
    echo Please install OpenSSL or set OPENSSL_ROOT_DIR environment variable
)

echo [RUN] IDL Build Script started
cd /d "%PROJECT_ROOT%\IDL"
echo [PATH] IDL folder: %CD%

REM Find all IDL files
set "IDL_COUNT=0"
for %%f in (*.idl) do (
    set /a IDL_COUNT+=1
    set "IDL_FILE_!IDL_COUNT!=%%f"
)

if %IDL_COUNT%==0 (
    echo [ERROR] No IDL files found in IDL folder!
    pause
    exit /b 1
)

echo [INFO] Found %IDL_COUNT% IDL files:
for /l %%i in (1,1,%IDL_COUNT%) do (
    call echo   - %%IDL_FILE_%%i%%
)
echo.

REM Process each IDL file
for /l %%i in (1,1,%IDL_COUNT%) do (
    call set "idl_file=%%IDL_FILE_%%i%%"
    call set "filename=%%idl_file:.idl=%%"
    call set "output_dir=%%filename%%_idl_generated"
    
    echo ========================================
    echo Processing: %%idl_file%%
    echo Output Directory: %%output_dir%%
    echo ========================================
    
    REM Create output directory
    if exist "%%output_dir%%" (
        echo [WARN] Directory %%output_dir%% already exists. Cleaning...
        rmdir /s /q "%%output_dir%%"
    )
    mkdir "%%output_dir%%"
    
    REM Generate code using fastddsgen
    echo [INFO] Generating DDS code...
    where fastddsgen >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] fastddsgen not found! Please install Fast DDS
        pause
        exit /b 1
    )
    
    fastddsgen -replace -example CMake -d "%%output_dir%%" "%%idl_file%%"
    if errorlevel 1 (
        echo [ERROR] fastddsgen failed for %%idl_file%%
        goto :continue_loop
    )
    
    REM Generate CMakeLists.txt
    echo [INFO] Generating CMakeLists.txt...
    cd "%%output_dir%%"
    
    (
        echo cmake_minimum_required(VERSION 3.16^)
        echo project(%%filename%%^)
        echo.
        echo # Find required packages
        echo find_package(fastcdr REQUIRED^)
        echo find_package(fastdds REQUIRED^)
        echo find_package(OpenSSL REQUIRED^)
        echo.
        echo # Set C++ standard
        echo set(CMAKE_CXX_STANDARD 17^)
        echo set(CMAKE_CXX_STANDARD_REQUIRED ON^)
        echo.
        echo # Include directories
        echo include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../include^)
        echo.
        echo # Create library
        echo file(GLOB_RECURSE LIB_SOURCES "*.cxx" "*.cpp"^)
        echo list(FILTER LIB_SOURCES EXCLUDE REGEX ".*main\\.cxx$"^)
        echo.
        echo if(LIB_SOURCES^)
        echo     add_library(%%filename%%_lib STATIC ${LIB_SOURCES}^)
        echo     target_link_libraries(%%filename%%_lib fastdds fastcdr OpenSSL::SSL OpenSSL::Crypto^)
        echo     target_include_directories(%%filename%%_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}^)
        echo     target_include_directories(%%filename%%_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../../include^)
        echo endif(^)
        echo.
        echo # Create executable
        echo file(GLOB_RECURSE MAIN_SOURCES "*main.cxx"^)
        echo if(MAIN_SOURCES^)
        echo     foreach(MAIN_SOURCE ${MAIN_SOURCES}^)
        echo         get_filename_component(EXEC_NAME ${MAIN_SOURCE} NAME_WE^)
        echo         add_executable(${EXEC_NAME} ${MAIN_SOURCE}^)
        echo         if(TARGET %%filename%%_lib^)
        echo             target_link_libraries(${EXEC_NAME} %%filename%%_lib fastdds fastcdr OpenSSL::SSL OpenSSL::Crypto^)
        echo         else(^)
        echo             target_link_libraries(${EXEC_NAME} fastdds fastcdr OpenSSL::SSL OpenSSL::Crypto^)
        echo         endif(^)
        echo     endforeach(^)
        echo endif(^)
    ) > CMakeLists.txt
    
    REM Build with CMake
    echo [INFO] Building with CMake...
    if not exist "build" mkdir "build"
    cd "build"
    
    cmake .. -DCMAKE_BUILD_TYPE=Release
    if errorlevel 1 (
        echo [ERROR] CMake configuration failed for %%filename%%
        cd ..\..
        goto :continue_loop
    )
    
    cmake --build . --config Release
    if errorlevel 1 (
        echo [ERROR] Build failed for %%filename%%
        cd ..\..
        goto :continue_loop
    )
    
    echo [OK] %%filename%% built successfully!
    cd ..\..
    echo.
    
    :continue_loop
)

echo ========================================
echo IDL Generation Completed!
echo ========================================
echo.
echo Summary:
for /l %%i in (1,1,%IDL_COUNT%) do (
    call set "idl_file=%%IDL_FILE_%%i%%"
    call set "filename=%%idl_file:.idl=%%"
    call set "output_dir=%%filename%%_idl_generated"
    if exist "%%output_dir%%\build" (
        echo   ✓ %%filename%%: Generated and Built
    ) else (
        echo   ✗ %%filename%%: Failed
    )
)
echo.
echo All IDL files have been processed!
echo.
pause
exit /b 0

