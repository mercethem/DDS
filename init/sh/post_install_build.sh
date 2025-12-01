#!/bin/bash
# DDS Project Post-Install Build Script
# This script runs after system dependencies are installed
# It handles Fast-DDS/npm installation and monitoring application build

# Get script directory and project root dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$INIT_DIR")"

# Walk up to find project root (contains IDL and scenarios)
CURRENT_DIR="$INIT_DIR"
while [ "$CURRENT_DIR" != "/" ] && [ "$CURRENT_DIR" != "." ]; do
    if [ -d "$CURRENT_DIR/IDL" ] && [ -d "$CURRENT_DIR/scenarios" ]; then
        PROJECT_ROOT="$CURRENT_DIR"
        break
    fi
    CURRENT_DIR="$(dirname "$CURRENT_DIR")"
done

# Run Fast-DDS auto installation script
echo "========================================"
echo "Running Fast-DDS Auto Installation..."
echo "========================================"
echo
if [ -f "$SCRIPT_DIR/fastdds_and_npm_auto_install.sh" ]; then
    bash "$SCRIPT_DIR/fastdds_and_npm_auto_install.sh"
else
    echo "[WARNING] fastdds_and_npm_auto_install.sh not found at $SCRIPT_DIR/fastdds_and_npm_auto_install.sh"
fi
echo

# Clean monitoring build directory and rebuild
echo "========================================"
echo "Cleaning and Building Monitoring Application..."
echo "========================================"
echo
MONITORING_BUILD_DIR="$PROJECT_ROOT/monitoring/build"
MONITORING_BUILD_SCRIPT="$PROJECT_ROOT/monitoring/build_monitoring/build_monitoring.sh"

if [ -d "$MONITORING_BUILD_DIR" ]; then
    echo "[INFO] Removing existing monitoring build directory..."
    rm -rf "$MONITORING_BUILD_DIR"
    echo "[INFO] Monitoring build directory removed."
else
    echo "[INFO] No existing monitoring build directory found."
fi

if [ -f "$MONITORING_BUILD_SCRIPT" ]; then
    echo "[INFO] Running build_monitoring.sh..."
    bash "$MONITORING_BUILD_SCRIPT"
else
    echo "[WARNING] build_monitoring.sh not found at $MONITORING_BUILD_SCRIPT"
fi
echo

