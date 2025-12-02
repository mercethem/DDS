#!/bin/bash
# DDS Project Post-Install Build Script
# This script runs after system dependencies are installed
# It handles Node.js installation, Fast-DDS installation, and monitoring application build

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

# Install Node.js if not already installed
echo "========================================"
echo "Checking and Installing Node.js..."
echo "========================================"
echo

NODEJS_INSTALLED=0
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
    echo "[INFO] Node.js is already installed: $NODE_VERSION"
    NODEJS_INSTALLED=1
elif command -v nodejs &> /dev/null; then
    NODE_VERSION=$(nodejs --version 2>/dev/null || echo "unknown")
    echo "[INFO] Node.js is already installed (as nodejs): $NODE_VERSION"
    NODEJS_INSTALLED=1
fi

if [ $NODEJS_INSTALLED -eq 0 ]; then
    echo "[INFO] Node.js not found, installing..."
    
    # Check if apt-get is available
    if command -v apt-get &> /dev/null; then
        # Try to install Node.js from Ubuntu repositories
        if sudo apt-get update > /dev/null 2>&1 && sudo apt-get install -y nodejs npm 2>/dev/null; then
            echo "[SUCCESS] Node.js installed from Ubuntu repositories"
            NODEJS_INSTALLED=1
        else
            # Fallback: Install Node.js using NodeSource repository (recommended)
            echo "[INFO] Installing Node.js from NodeSource repository..."
            if command -v curl &> /dev/null; then
                curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - > /dev/null 2>&1
                if sudo apt-get install -y nodejs 2>/dev/null; then
                    echo "[SUCCESS] Node.js installed from NodeSource repository"
                    NODEJS_INSTALLED=1
                else
                    echo "[WARNING] Failed to install Node.js from NodeSource repository"
                fi
            else
                echo "[WARNING] curl not found, cannot install Node.js from NodeSource"
            fi
        fi
    else
        echo "[WARNING] apt-get not found, cannot install Node.js automatically"
    fi
    
    if [ $NODEJS_INSTALLED -eq 1 ]; then
        # Verify installation
        if command -v node &> /dev/null; then
            NODE_VERSION=$(node --version)
            echo "[INFO] Node.js version: $NODE_VERSION"
        fi
        if command -v npm &> /dev/null; then
            NPM_VERSION=$(npm --version)
            echo "[INFO] npm version: $NPM_VERSION"
        fi
    fi
fi

echo

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

