#!/bin/bash
# DDS Project Dependency Installation Script for Ubuntu/Debian

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

echo "========================================"
echo "DDS Project - Ubuntu Dependencies Installer"
echo "========================================"
echo

# Root check
if [[ $EUID -eq 0 ]]; then
   echo "[ERROR] This script should not be run as root!"
   echo "Please run as normal user (sudo will be asked automatically when needed)"
   exit 1
fi

# Check Ubuntu version
UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "unknown")
echo "[INFO] Ubuntu version: $UBUNTU_VERSION"

# System update
echo "[STEP 1/6] Updating system packages..."
sudo apt update

# Basic build tools
echo "[STEP 2/6] Installing basic build tools..."
sudo apt install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    curl \
    wget \
    unzip

# Python and Java
echo "[STEP 3/6] Installing Python and Java..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-tk \
    python3-dev \
    openjdk-11-jdk

# Library dependencies
echo "[STEP 4/6] Installing library dependencies..."
sudo apt install -y \
    libssl-dev \
    libtinyxml2-dev \
    libfoonathan-memory-dev \
    libasio-dev \
    libboost-dev

# Fast-DDS installation (from package manager for Ubuntu 20.04+)
echo "[STEP 5/6] Installing Fast-DDS..."
if [[ $(echo "$UBUNTU_VERSION >= 20.04" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
    echo "[INFO] Ubuntu 20.04+ detected, installing from package manager..."
    sudo apt install -y \
        libfastcdr-dev \
        libfastdds-dev \
        fastddsgen
else
    echo "[INFO] Pre-Ubuntu 20.04 detected, source code installation required..."
    echo "[WARNING] Please follow the manual installation instructions in REQUIREMENTS_LINUX.md"
fi

# Setting environment variables
echo "[STEP 6/6] Setting environment variables..."

# Set JAVA_HOME
JAVA_HOME_PATH="/usr/lib/jvm/java-11-openjdk-amd64"
if [ ! -d "$JAVA_HOME_PATH" ]; then
    JAVA_HOME_PATH="/usr/lib/jvm/java-11-openjdk"
fi

# Add to .bashrc (if not already present)
if ! grep -q "# DDS Project Environment" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# DDS Project Environment" >> ~/.bashrc
    echo "export JAVA_HOME=$JAVA_HOME_PATH" >> ~/.bashrc
    echo "export PATH=\$PATH:\$JAVA_HOME/bin" >> ~/.bashrc
    echo "export FASTDDS_HOME=/usr/local" >> ~/.bashrc
    echo "export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH" >> ~/.bashrc
    echo "export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:\$PKG_CONFIG_PATH" >> ~/.bashrc
    echo "[INFO] Environment variables added to ~/.bashrc"
else
    echo "[INFO] Environment variables already present"
fi

# Update library cache
sudo ldconfig

echo
echo "========================================"
echo "Installation Completed!"
echo "========================================"
echo
echo "Next steps:"
echo "1. Restart terminal or run: source ~/.bashrc"
echo "2. Test installation: ./test_installation.sh"
echo "3. Run project: $PROJECT_ROOT/scripts/sh/run_complete_workflow.sh"
echo
echo "Note: Pre-Ubuntu 20.04 versions may require manual Fast-DDS installation."
echo "See REQUIREMENTS_LINUX.md for details."
echo

# Run post-install build script (Fast-DDS/npm installation and monitoring build)
if [ -f "$SCRIPT_DIR/post_install_build.sh" ]; then
    bash "$SCRIPT_DIR/post_install_build.sh"
else
    echo "[WARNING] post_install_build.sh not found at $SCRIPT_DIR/post_install_build.sh"
fi

