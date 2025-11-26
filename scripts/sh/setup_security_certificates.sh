#!/bin/bash
echo "========================================"
echo "DDS Security Complete Setup - Dynamic Version"
echo "========================================"
echo

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
    echo "[WARN] Secure DDS folder not found, creating..."
    mkdir -p "$PROJECT_ROOT/secure_dds/CA"
    mkdir -p "$PROJECT_ROOT/secure_dds/participants"
fi

if [ ! -d "$PROJECT_ROOT/docs" ]; then
    echo "[WARN] Docs folder not found, creating..."
    mkdir -p "$PROJECT_ROOT/docs"
fi

echo "[OK] Project structure is portable"
echo

# Find Python dynamically
echo "[INFO] Searching for Python installation..."
bash "${SCRIPT_DIR}/find_tools.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] Python not found!"
    exit 1
fi

# Source the environment to get DETECTED_PYTHON_PATH
if [ -f "$PROJECT_ROOT/scripts/py/detected_environment.sh" ]; then
    source "$PROJECT_ROOT/scripts/py/detected_environment.sh"
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

# Check if generate_security_certificates.py exists
if [ ! -f "$PROJECT_ROOT/scripts/py/generate_security_certificates.py" ]; then
    echo "[ERROR] generate_security_certificates.py not found!"
    echo "Please make sure the file exists in the scripts/py folder."
    exit 1
fi

# Run certificate generation
echo "[INFO] Generating DDS Security certificates..."
cd "$PROJECT_ROOT/scripts/py" && $PYTHON_CMD generate_security_certificates.py
CERT_EXIT_CODE=$?

if [ $CERT_EXIT_CODE -eq 0 ]; then
    echo "[OK] Certificate generation completed successfully!"
else
    echo "[ERROR] Certificate generation failed with exit code $CERT_EXIT_CODE!"
    exit 1
fi

echo
echo "========================================"
echo "[STEP 2] Security Configuration"
echo "========================================"

# Check if apply_security_settings.py exists
if [ ! -f "$PROJECT_ROOT/scripts/py/apply_security_settings.py" ]; then
    echo "[ERROR] apply_security_settings.py not found!"
    echo "Please make sure the file exists in the scripts/py folder."
    exit 1
fi

# Run security configuration
echo "[INFO] Applying DDS Security configuration..."
cd "$PROJECT_ROOT/scripts/py" && $PYTHON_CMD apply_security_settings.py
SEC_EXIT_CODE=$?

if [ $SEC_EXIT_CODE -eq 0 ]; then
    echo "[OK] Security configuration completed successfully!"
else
    echo "[ERROR] Security configuration failed with exit code $SEC_EXIT_CODE!"
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
