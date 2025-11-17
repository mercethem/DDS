#!/bin/bash
# Dynamic ALL Script - Complete DDS Workflow
# This script runs all DDS processes with dynamic detection

echo "========================================"
echo "Dynamic DDS Complete Workflow"
echo "========================================"
echo

# Get script directory
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

if [ ! -d "../../certs" ]; then
    echo "[WARN] Certs folder not found, creating..."
    # certs folder is no longer used - secure_dds system is used
fi

if [ ! -d "../../docs" ]; then
    echo "[WARN] Docs folder not found, creating..."
    mkdir -p "../../docs"
fi

echo "[OK] Project structure is portable"
echo

# Step 1: Environment Setup
echo "========================================"
echo "[STEP 1] Environment Setup"
echo "========================================"
bash "${SCRIPT_DIR}/dynamic_environment_setup.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] Environment Setup failed!"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "[OK] Environment Setup completed!"
echo

# Step 2: IDL Generation
echo "========================================"
echo "[STEP 2] IDL Generation"
echo "========================================"
bash "${SCRIPT_DIR}/IDL_GENERATOR.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] IDL Generation failed!"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "[OK] IDL Generation completed!"
echo

# Step 3: Domain ID Update
echo "========================================"
echo "[STEP 3] Domain ID Update"
echo "========================================"
bash "${SCRIPT_DIR}/update_domain_ids_dynamic.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] Domain ID Update failed!"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "[OK] Domain ID Update completed!"
echo

# Step 4: Security Setup
echo "========================================"
echo "[STEP 4] Security Setup"
echo "========================================"
bash "${SCRIPT_DIR}/dynamic_security_certificate.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] Security Setup failed!"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "[OK] Security Setup completed!"
echo

# Step 5: IDL Patcher Setup
echo "========================================"
echo "[STEP 5] IDL Patcher Setup"
echo "========================================"
bash "${SCRIPT_DIR}/idl_patcher.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] IDL Patcher failed!"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "[OK] IDL Patcher completed!"
echo

# Step 6: IDL Setup Patcher
echo "========================================"
echo "[STEP 6] IDL Setup Patcher"
echo "========================================"
bash "${SCRIPT_DIR}/idl_setup_patcher.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] IDL Setup Patcher failed!"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "[OK] IDL Setup Patcher completed!"
echo

# Step 7: JSON Patcher
echo "========================================"
echo "[STEP 7] JSON Patcher"
echo "========================================"
bash "${SCRIPT_DIR}/json_patcher.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] JSON Patcher failed!"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "[OK] JSON Patcher completed!"
echo

# Step 8: IDL Building
echo "========================================"
echo "[STEP 8] IDL Building"
echo "========================================"
bash "${SCRIPT_DIR}/IDL_BUILDER.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] IDL Building failed!"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "[OK] IDL Building completed!"
echo

# Step 9: Module Detection
echo "========================================"
echo "[STEP 9] Module Detection"
echo "========================================"
bash "${SCRIPT_DIR}/dynamic_finder.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] Module Detection failed!"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "[OK] Module Detection completed!"
echo

# Step 10: Testing (Optional)
echo "========================================"
echo "[STEP 10] Testing (Optional)"
echo "========================================"
echo "[INFO] Would you like to run tests? (Y/N)"
read -p "Enter choice: " RUN_TESTS
if [[ "${RUN_TESTS^^}" == "Y" ]]; then
    bash "${SCRIPT_DIR}/simple_dynamic_test.sh"
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
read -p "Press Enter to continue..."