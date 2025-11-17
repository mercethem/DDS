#!/bin/bash
echo "========================================"
echo "DDS Security Complete Setup - Dynamic Version"
echo "========================================"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Portability check
echo "[INFO] Running portability checks..."

# Check required folders
if [ ! -d "../../IDL" ]; then
    echo "[ERROR] IDL folder not found!"
    echo "This file must be executed from the scripts/sh folder."
    read -p "Press Enter to continue..."
    exit 1
fi

if [ ! -d "../../secure_dds" ]; then
    echo "[WARN] Secure DDS folder not found, creating..."
    mkdir -p "../../secure_dds/CA"
    mkdir -p "../../secure_dds/participants"
fi

if [ ! -d "../../docs" ]; then
    echo "[WARN] Docs folder not found, creating..."
    mkdir -p "../../docs"
fi

echo "[OK] Project structure is portable"
echo

# Find Python dynamically
echo "[INFO] Searching for Python installation..."
bash "${SCRIPT_DIR}/dynamic_finder.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] Python not found!"
    read -p "Press Enter to continue..."
    exit 1
fi

# Source the environment to get DETECTED_PYTHON_PATH
if [ -f "../py/detected_environment.sh" ]; then
    source "../py/detected_environment.sh"
fi

# Use python3 as default if DETECTED_PYTHON_PATH is not set
PYTHON_CMD="${DETECTED_PYTHON_PATH:-python3}"
echo "[OK] Using Python: $PYTHON_CMD"
echo

echo "This script fully configures DDS Security:"
echo "1. Generates certificates"
echo "2. Applies security settings"
echo "3. Prepares the system"
echo
echo "========================================"
echo "[STEP 1] Certificate Generation"
echo "========================================"

# Check if certificate.py exists
if [ ! -f "../py/certificate.py" ]; then
    echo "[ERROR] certificate.py not found!"
    echo "Please make sure the file exists in the scripts/py folder."
    read -p "Press Enter to continue..."
    exit 1
fi

# Run certificate generation
echo "[INFO] Generating DDS Security certificates..."
cd "../py" && $PYTHON_CMD certificate.py
CERT_EXIT_CODE=$?

if [ $CERT_EXIT_CODE -eq 0 ]; then
    echo "[OK] Certificate generation completed successfully!"
else
    echo "[ERROR] Certificate generation failed with exit code $CERT_EXIT_CODE!"
    read -p "Press Enter to continue..."
    exit 1
fi

echo
echo "========================================"
echo "[STEP 2] Security Configuration"
echo "========================================"

# Check if security.py exists
if [ ! -f "../py/security.py" ]; then
    echo "[ERROR] security.py not found!"
    echo "Please make sure the file exists in the scripts/py folder."
    read -p "Press Enter to continue..."
    exit 1
fi

# Run security configuration
echo "[INFO] Applying DDS Security configuration..."
$PYTHON_CMD security.py
SEC_EXIT_CODE=$?

if [ $SEC_EXIT_CODE -eq 0 ]; then
    echo "[OK] Security configuration completed successfully!"
else
    echo "[ERROR] Security configuration failed with exit code $SEC_EXIT_CODE!"
    read -p "Press Enter to continue..."
    exit 1
fi

echo
echo "========================================"
echo "DDS Security Setup Completed!"
echo "========================================"
echo
echo "Summary:"
echo "  - Certificate Generation: OK"
echo "  - Security Configuration: OK"
echo "  - System is ready for secure DDS communication"
echo
echo "Your DDS system now has security enabled!"

exit 0
read -p "Press Enter to continue..."