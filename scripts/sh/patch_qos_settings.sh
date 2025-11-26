#!/bin/bash
# Dynamic QoS Patcher - Portable QoS Configuration
# This script runs QoS patcher with dynamic Python detection

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

cd "$SCRIPT_DIR"

echo "========================================"
echo "Dynamic QoS Patcher GUI Starting..."
echo "========================================"
echo

# Find Python dynamically
echo "[INFO] Searching for Python installation..."
bash "${SCRIPT_DIR}/find_tools.sh"
if [ $? -ne 0 ]; then
    echo "[ERROR] Python not found!"
    read -p "Press Enter to continue..."
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

# Check if QoS patcher GUI exists
if [ ! -f "$PROJECT_ROOT/scripts/py/qos_settings_patcher_gui.py" ]; then
    echo "[ERROR] qos_settings_patcher_gui.py not found!"
    echo "Please make sure the file exists in the scripts/py folder."
    read -p "Press Enter to continue..."
    exit 1
fi

# Run QoS patcher GUI
echo "[STEP] Starting QoS Patcher GUI..."
cd "$PROJECT_ROOT/scripts/py" && $PYTHON_CMD qos_settings_patcher_gui.py
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