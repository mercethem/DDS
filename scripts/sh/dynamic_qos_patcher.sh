#!/bin/bash
# Dynamic QoS Patcher - Portable QoS Configuration
# This script runs QoS patcher with dynamic Python detection

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "Dynamic QoS Patcher GUI Starting..."
echo "========================================"
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

# Check if QoS patcher GUI exists
if [ ! -f "../py/qos_patcher_gui.py" ]; then
    echo "[ERROR] qos_patcher_gui.py not found!"
    echo "Please make sure the file exists in the scripts folder."
    read -p "Press Enter to continue..."
    exit 1
fi

# Run QoS patcher GUI
echo "[STEP] Starting QoS Patcher GUI..."
cd "../py" && $PYTHON_CMD qos_patcher_gui.py
EXIT_CODE=$?

echo
echo "========================================"
echo "QoS Patcher GUI finished."
echo "========================================"
echo

if [ $EXIT_CODE -eq 0 ]; then
    echo "[OK] QoS Patcher completed successfully!"
else
    echo "[ERROR] QoS Patcher failed with exit code $EXIT_CODE!"
fi

echo
read -p "Press Enter to continue..."