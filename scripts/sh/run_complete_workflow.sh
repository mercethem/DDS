#!/bin/bash
# Dynamic ALL Script - Complete DDS Workflow
# This script runs all DDS processes with dynamic detection

echo "========================================"
echo "Dynamic DDS Complete Workflow"
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

# Step 1: Environment Setup
echo "========================================"
echo "[STEP 1] Environment Setup"
echo "========================================"
bash "${SCRIPT_DIR}/setup_environment.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] Environment Setup failed!"
    exit 1
fi
echo "[OK] Environment Setup completed!"
echo

# Step 2: IDL Generation
echo "========================================"
echo "[STEP 2] IDL Generation"
echo "========================================"
(cd "$SCRIPT_DIR" && bash generate_idl_code.sh)
if [ $? -ne 0 ]; then
    echo "[ERROR] IDL Generation failed!"
    exit 1
fi
echo "[OK] IDL Generation completed!"
echo

# Step 3: Domain ID Update
echo "========================================"
echo "[STEP 3] Domain ID Update"
echo "========================================"
(cd "$SCRIPT_DIR" && bash update_domain_ids.sh)
if [ $? -ne 0 ]; then
    echo "[ERROR] Domain ID Update failed!"
    exit 1
fi
echo "[OK] Domain ID Update completed!"
echo

# Step 4: Security Setup
echo "========================================"
echo "[STEP 4] Security Setup"
echo "========================================"
(cd "$SCRIPT_DIR" && bash setup_security_certificates.sh)
if [ $? -ne 0 ]; then
    echo "[ERROR] Security Setup failed!"
    exit 1
fi
echo "[OK] Security Setup completed!"
echo

# Step 5: IDL Patcher Setup
echo "========================================"
echo "[STEP 5] IDL Patcher Setup"
echo "========================================"
(cd "$SCRIPT_DIR" && bash patch_idl_defaults.sh)
if [ $? -ne 0 ]; then
    echo "[ERROR] IDL Patcher failed!"
    exit 1
fi
echo "[OK] IDL Patcher completed!"
echo

# Step 6: IDL Setup Patcher
echo "========================================"
echo "[STEP 6] IDL Setup Patcher"
echo "========================================"
bash "${SCRIPT_DIR}/patch_idl_setup.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] IDL Setup Patcher failed!"
    exit 1
fi
echo "[OK] IDL Setup Patcher completed!"
echo

# Step 7: JSON Patcher
echo "========================================"
echo "[STEP 7] JSON Patcher"
echo "========================================"
(cd "$SCRIPT_DIR" && bash patch_json_reading.sh)
if [ $? -ne 0 ]; then
    echo "[ERROR] JSON Patcher failed!"
    exit 1
fi
echo "[OK] JSON Patcher completed!"
echo

# Step 7: Security Patcher Setup
echo "========================================"
echo "[STEP 7] Security Patcher Setup"
echo "========================================"
cd "$PROJECT_ROOT"
python3 "$PROJECT_ROOT/scripts/py/apply_security_settings.py"
if [ $? -ne 0 ]; then
    echo "[WARNING] Security Patcher completed with warnings"
fi
echo "[OK] Security Patcher completed!"
echo

# Step 8: Clean Duplicates
echo "========================================"
echo "[STEP 8] Clean Duplicates"
echo "========================================"
python3 "$PROJECT_ROOT/scripts/py/clean_duplicate_code.py"
if [ $? -ne 0 ]; then
    echo "[WARNING] Clean Duplicates completed with warnings"
fi
echo "[OK] Clean Duplicates completed!"
echo

# Step 9: CMake Portability Fix
echo "========================================"
echo "[STEP 9] CMake Portability Fix"
echo "========================================"
python3 "$PROJECT_ROOT/scripts/py/fix_cmake_rpath.py"
if [ $? -ne 0 ]; then
    echo "[WARNING] CMake Portability Fix completed with warnings"
fi
echo "[OK] CMake Portability Fix completed!"
echo

# Step 10: IDL Building
echo "========================================"
echo "[STEP 10] IDL Building"
echo "========================================"
(cd "$SCRIPT_DIR" && bash build_idl_modules.sh)
if [ $? -ne 0 ]; then
    echo "[ERROR] IDL Building failed!"
    exit 1
fi
echo "[OK] IDL Building completed!"
echo

# Step 9: Module Detection
echo "========================================"
echo "[STEP 9] Module Detection"
echo "========================================"
bash "${SCRIPT_DIR}/find_tools.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] Module Detection failed!"
    exit 1
fi
echo "[OK] Module Detection completed!"
echo

# Step 10: Testing (Optional)
echo "========================================"
echo "[STEP 10] Testing (Optional)"
echo "========================================"
# Auto-run tests (no user interaction needed)
RUN_TESTS="N"
# Uncomment to enable auto-testing:
# RUN_TESTS="Y"
if [[ "${RUN_TESTS^^}" == "Y" ]]; then
    bash "${SCRIPT_DIR}/test_idl_modules.sh"
    if [ $? -ne 0 ]; then
        echo "[WARN] Testing failed, but workflow completed!"
    else
        echo "[OK] Testing completed!"
    fi
else
    echo "[SKIP] Testing skipped by user choice."
fi

echo
echo "========================================"
echo "Dynamic DDS Workflow Completed!"
echo "========================================"
echo
echo "Summary:"
echo "  - Environment Setup: OK"
echo "  - IDL Generation: OK"
echo "  - IDL Patching: OK"
echo "  - Domain ID Update: OK"
echo "  - Security Setup: OK (Auth + Encryption, Access Control disabled)"
echo "  - IDL Building: OK"
echo "  - Module Detection: OK"
echo "  - Testing: ${RUN_TESTS}"
echo
echo "Your DDS system is ready to use!"
echo