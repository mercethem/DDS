#!/bin/bash
# Fast DDS IDL Generator - Portable Version

echo "========================================"
echo "Fast DDS IDL Generator - Portable Version"
echo "========================================"
echo

# Get script directory and project root dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Walk up to find project root (contains IDL and scenarios)
CURRENT_DIR="$SCRIPT_DIR"
while [ "$CURRENT_DIR" != "/" ] && [ "$CURRENT_DIR" != "." ]; do
    if [ -d "$CURRENT_DIR/IDL" ] && [ -d "$CURRENT_DIR/scenarios" ]; then
        PROJECT_ROOT="$CURRENT_DIR"
        break
    fi
    CURRENT_DIR="$(dirname "$CURRENT_DIR")"
done

# Portability check
echo "[INFO] Running portability checks..."

# Check required folders
if [ ! -d "$PROJECT_ROOT/IDL" ]; then
    echo "[ERROR] IDL folder not found!"
    echo "Project root: $PROJECT_ROOT"
    exit 1
fi

if [ ! -d "$PROJECT_ROOT/secure_dds" ]; then
    echo "[WARN] secure_dds folder not found, will be created when needed..."
    # secure_dds folder will be created by generate_security_certificates.py
fi

echo "[OK] Project structure is portable"
echo

# Java check
if ! command -v java &> /dev/null; then
    echo "[ERROR] Java is not installed!"
    exit 1
fi

JAVA_PATH=$(which java)
echo "[OK] Java found: $JAVA_PATH"

# JSON library check and setup
echo "[INFO] Checking JSON library..."
JSON_INCLUDE_DIR="$PROJECT_ROOT/include/nlohmann"
JSON_HEADER="$JSON_INCLUDE_DIR/json.hpp"

if [ ! -f "$JSON_HEADER" ]; then
    echo "[INFO] JSON library not found, downloading..."
    mkdir -p "$JSON_INCLUDE_DIR"
    
    if command -v wget &> /dev/null; then
        wget -O "$JSON_HEADER" "https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp"
        if [ $? -eq 0 ]; then
            echo "[OK] JSON library downloaded successfully"
        else
            echo "[ERROR] Failed to download JSON library"
            exit 1
        fi
    elif command -v curl &> /dev/null; then
        curl -L -o "$JSON_HEADER" "https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp"
        if [ $? -eq 0 ]; then
            echo "[OK] JSON library downloaded successfully"
        else
            echo "[ERROR] Failed to download JSON library"
            exit 1
        fi
    else
        echo "[ERROR] Neither wget nor curl found! Cannot download JSON library"
        exit 1
    fi
else
    echo "[OK] JSON library found: $JSON_HEADER"
fi

# Find OpenSSL paths dynamically (portability)
echo "[INFO] Searching for OpenSSL paths..."

OPENSSL_ROOT_DIR=""
OPENSSL_LIB_DIR=""
OPENSSL_INCLUDE_DIR=""

# 1. Check pkg-config first (most common on Linux)
if command -v pkg-config &> /dev/null && pkg-config --exists openssl; then
    OPENSSL_ROOT_DIR=$(pkg-config --variable=prefix openssl)
    OPENSSL_LIB_DIR=$(pkg-config --variable=libdir openssl)
    OPENSSL_INCLUDE_DIR=$(pkg-config --variable=includedir openssl)
    echo "[OK] OpenSSL found via pkg-config: $OPENSSL_ROOT_DIR"
elif [ -d "/usr/lib/x86_64-linux-gnu" ] && [ -d "/usr/include/openssl" ]; then
    # 2. Ubuntu/Debian standard paths
    OPENSSL_ROOT_DIR="/usr"
    OPENSSL_LIB_DIR="/usr/lib/x86_64-linux-gnu"
    OPENSSL_INCLUDE_DIR="/usr/include"
    echo "[OK] OpenSSL found in system paths: $OPENSSL_ROOT_DIR"
elif [ -d "/usr/local/lib" ] && [ -d "/usr/local/include/openssl" ]; then
    # 3. Local installation
    OPENSSL_ROOT_DIR="/usr/local"
    OPENSSL_LIB_DIR="/usr/local/lib"
    OPENSSL_INCLUDE_DIR="/usr/local/include"
    echo "[OK] OpenSSL found in local paths: $OPENSSL_ROOT_DIR"
else
    echo "[ERROR] OpenSSL not found!"
    echo "Please install OpenSSL development packages:"
    echo "  Ubuntu/Debian: sudo apt-get install libssl-dev"
    echo "  CentOS/RHEL: sudo yum install openssl-devel"
    echo "  Fedora: sudo dnf install openssl-devel"
    exit 1
fi

echo "[RUN] IDL Build Script started"
cd "$PROJECT_ROOT/IDL"
echo "[PATH] IDL folder: $(pwd)"

# Find all IDL files
IDL_FILES=(*.idl)
if [ ${#IDL_FILES[@]} -eq 0 ] || [ ! -f "${IDL_FILES[0]}" ]; then
    echo "[ERROR] No IDL files found in IDL folder!"
    exit 1
fi

echo "[INFO] Found ${#IDL_FILES[@]} IDL files:"
for idl_file in "${IDL_FILES[@]}"; do
    echo "  - $idl_file"
done
echo

# Process each IDL file
for idl_file in "${IDL_FILES[@]}"; do
    if [ -f "$idl_file" ]; then
        filename=$(basename "$idl_file" .idl)
        output_dir="${filename}_idl_generated"
        
        echo "========================================"
        echo "Processing: $idl_file"
        echo "Output Directory: $output_dir"
        echo "========================================"
        
        # Create output directory
        if [ -d "$output_dir" ]; then
            echo "[WARN] Directory $output_dir already exists. Cleaning..."
            rm -rf "$output_dir"
        fi
        mkdir -p "$output_dir"
        
        # Generate code using fastddsgen
        echo "[INFO] Generating DDS code..."
        if command -v fastddsgen &> /dev/null; then
            fastddsgen -replace -example CMake -d "$output_dir" "$idl_file"
            if [ $? -ne 0 ]; then
                echo "[ERROR] fastddsgen failed for $idl_file"
                continue
            fi
        else
            echo "[ERROR] fastddsgen not found! Please install Fast DDS"
            exit 1
        fi
        
        # Generate CMakeLists.txt
        echo "[INFO] Generating CMakeLists.txt..."
        cd "$output_dir"
        
        cat > CMakeLists.txt << EOF
cmake_minimum_required(VERSION 3.16)
project(${filename})

# Find required packages
find_package(fastcdr REQUIRED)
find_package(fastdds REQUIRED)
find_package(OpenSSL REQUIRED)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Portable binary settings - RPATH for shared libraries
# Use relative RPATH so binaries work when moved to different locations
set(CMAKE_BUILD_RPATH_USE_ORIGIN TRUE)  # Use \$ORIGIN for relative paths
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH FALSE)
# Add common library paths to RPATH (relative to executable)
set(CMAKE_BUILD_RPATH "\$ORIGIN/../lib:\$ORIGIN/../../lib:/usr/local/lib")

# Include directories
include_directories(\${CMAKE_CURRENT_SOURCE_DIR}/../../include)

# Create library
file(GLOB_RECURSE LIB_SOURCES "*.cxx" "*.cpp")
list(FILTER LIB_SOURCES EXCLUDE REGEX ".*main\\.cxx$")

if(LIB_SOURCES)
    add_library(${filename}_lib STATIC \${LIB_SOURCES})
    target_link_libraries(${filename}_lib fastdds fastcdr OpenSSL::SSL OpenSSL::Crypto)
    target_include_directories(${filename}_lib PUBLIC \${CMAKE_CURRENT_SOURCE_DIR})
    target_include_directories(${filename}_lib PUBLIC \${CMAKE_CURRENT_SOURCE_DIR}/../../include)
endif()

# Create executable
file(GLOB_RECURSE MAIN_SOURCES "*main.cxx")
if(MAIN_SOURCES)
    foreach(MAIN_SOURCE \${MAIN_SOURCES})
        get_filename_component(EXEC_NAME \${MAIN_SOURCE} NAME_WE)
        add_executable(\${EXEC_NAME} \${MAIN_SOURCE})
        
        # Set RPATH for portable binaries (relative to executable location)
        set_target_properties(\${EXEC_NAME} PROPERTIES
            BUILD_RPATH "\$ORIGIN/../lib:\$ORIGIN/../../lib"
            INSTALL_RPATH "\$ORIGIN/../lib:\$ORIGIN/../../lib"
            BUILD_WITH_INSTALL_RPATH FALSE
            INSTALL_WITH_INSTALL_RPATH FALSE
        )
        
        if(TARGET ${filename}_lib)
            target_link_libraries(\${EXEC_NAME} ${filename}_lib fastdds fastcdr OpenSSL::SSL OpenSSL::Crypto)
        else()
            target_link_libraries(\${EXEC_NAME} fastdds fastcdr OpenSSL::SSL OpenSSL::Crypto)
        endif()
    endforeach()
endif()
EOF
        
        # Build with CMake
        echo "[INFO] Building with CMake..."
        mkdir -p build
        cd build
        
        cmake .. -DCMAKE_BUILD_TYPE=Release
        if [ $? -ne 0 ]; then
            echo "[ERROR] CMake configuration failed for $filename"
            cd "$PROJECT_ROOT/IDL"
            continue
        fi
        
        make -j$(nproc)
        if [ $? -ne 0 ]; then
            echo "[ERROR] Build failed for $filename"
            cd "$PROJECT_ROOT/IDL"
            continue
        fi
        
        echo "[OK] $filename built successfully!"
        cd "$PROJECT_ROOT/IDL"
        echo
    fi
done

echo "========================================"
echo "IDL Generation Completed!"
echo "========================================"
echo
echo "Summary:"
for idl_file in "${IDL_FILES[@]}"; do
    if [ -f "$idl_file" ]; then
        filename=$(basename "$idl_file" .idl)
        output_dir="${filename}_idl_generated"
        if [ -d "$output_dir/build" ]; then
            echo "  ✓ $filename: Generated and Built"
        else
            echo "  ✗ $filename: Failed"
        fi
    fi
done
echo
echo "All IDL files have been processed!"

# Run JSON patcher if scenarios directory exists (DISABLED - conflicts with IDL Patcher)
# SCENARIOS_DIR="$PROJECT_ROOT/scenarios"
# if [ -d "$SCENARIOS_DIR" ]; then
#     echo
#     echo "========================================"
#     echo "Running JSON Patcher..."
#     echo "========================================"
#     
#     PYTHON_SCRIPT="$SCRIPT_DIR/../py/json_reading_patcher.py"
#     if [ -f "$PYTHON_SCRIPT" ]; then
#         cd "$PROJECT_ROOT"
#         python3 "$PYTHON_SCRIPT"
#         if [ $? -eq 0 ]; then
#             echo "[OK] JSON patcher completed!"
#         else
#             echo "[WARNING] JSON patcher completed with warnings"
#         fi
#     else
#         echo "[WARNING] JSON patcher script not found: $PYTHON_SCRIPT"
#     fi
# else
#     echo "[INFO] Scenarios directory not found, skipping JSON patcher"
# fi
echo "[INFO] JSON Patcher disabled to prevent conflicts with IDL Patcher"


echo
echo "========================================"
echo "IDL Generation Completed!"
echo "========================================"
echo
echo "Summary:"
for idl_file in "$IDL_DIR"/*.idl; do
    if [ -f "$idl_file" ]; then
        filename=$(basename "$idl_file" .idl)
        echo "  ✓ $filename: Generated and Built"
    fi
done
echo
echo "All IDL files have been processed!"
echo

exit 0