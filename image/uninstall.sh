#!/bin/bash
# DDS Project - Uninstall Script
# This script helps remove DDS Project and optionally system dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "========================================"
    echo "  DDS Project - Uninstaller"
    echo "  Version: v1.0.0_alpha"
    echo "========================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_banner

echo "This script will help you uninstall the DDS Project."
echo ""
echo "What would you like to remove?"
echo ""

# Check what's installed
PROJECT_EXISTS=0
SYSTEM_PACKAGES_INSTALLED=0
ENV_VARS_EXIST=0

if [ -d "$PROJECT_ROOT" ] && [ -d "$PROJECT_ROOT/IDL" ]; then
    PROJECT_EXISTS=1
fi

if command -v dpkg &> /dev/null; then
    if dpkg -l | grep -q "libfastdds-dev\|fastddsgen"; then
        SYSTEM_PACKAGES_INSTALLED=1
    fi
fi

if [ -f ~/.bashrc ] && grep -q "# DDS Project Environment" ~/.bashrc; then
    ENV_VARS_EXIST=1
fi

# Show what's found
echo "Found:"
if [ $PROJECT_EXISTS -eq 1 ]; then
    echo "  ✓ DDS Project directory: $PROJECT_ROOT"
else
    echo "  ✗ DDS Project directory not found"
fi

if [ $SYSTEM_PACKAGES_INSTALLED -eq 1 ]; then
    echo "  ✓ System packages installed (Fast-DDS, etc.)"
else
    echo "  ✗ System packages not detected (or not installed via apt)"
fi

if [ $ENV_VARS_EXIST -eq 1 ]; then
    echo "  ✓ Environment variables in ~/.bashrc"
else
    echo "  ✗ Environment variables not found"
fi

echo ""

# Options
REMOVE_PROJECT=0
REMOVE_PACKAGES=0
REMOVE_ENV_VARS=0

# Ask about project directory
if [ $PROJECT_EXISTS -eq 1 ]; then
    read -p "Remove DDS Project directory? (y/N): " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        REMOVE_PROJECT=1
    fi
fi

# Ask about system packages
if [ $SYSTEM_PACKAGES_INSTALLED -eq 1 ]; then
    echo ""
    echo "⚠ WARNING: Removing system packages may affect other projects!"
    read -p "Remove system packages (Fast-DDS, CMake, etc.)? (y/N): " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        REMOVE_PACKAGES=1
    fi
fi

# Ask about environment variables
if [ $ENV_VARS_EXIST -eq 1 ]; then
    echo ""
    read -p "Remove environment variables from ~/.bashrc? (y/N): " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        REMOVE_ENV_VARS=1
    fi
fi

echo ""
echo "========================================"
echo "  Uninstall Summary"
echo "========================================"
echo ""

# Remove project directory
if [ $REMOVE_PROJECT -eq 1 ]; then
    print_info "Removing project directory: $PROJECT_ROOT"
    if [ -d "$PROJECT_ROOT" ]; then
        read -p "Are you sure you want to delete $PROJECT_ROOT? (yes/NO): " confirm
        if [ "$confirm" = "yes" ]; then
            rm -rf "$PROJECT_ROOT"
            print_success "Project directory removed"
        else
            print_warning "Project directory removal cancelled"
        fi
    else
        print_warning "Project directory not found"
    fi
else
    print_info "Skipping project directory removal"
fi

# Remove system packages
if [ $REMOVE_PACKAGES -eq 1 ]; then
    print_info "Removing system packages..."
    
    if command -v apt-get &> /dev/null; then
        echo ""
        echo "The following packages will be removed:"
        echo "  - libfastcdr-dev libfastdds-dev fastddsgen"
        echo "  - build-essential cmake"
        echo "  - python3 python3-pip python3-tk python3-dev"
        echo "  - openjdk-11-jdk"
        echo "  - libssl-dev libtinyxml2-dev libfoonathan-memory-dev libasio-dev libboost-dev"
        echo ""
        read -p "Continue? (yes/NO): " confirm
        
        if [ "$confirm" = "yes" ]; then
            sudo apt-get remove --purge -y \
                libfastcdr-dev \
                libfastdds-dev \
                fastddsgen \
                build-essential \
                cmake \
                python3 \
                python3-pip \
                python3-tk \
                python3-dev \
                openjdk-11-jdk \
                libssl-dev \
                libtinyxml2-dev \
                libfoonathan-memory-dev \
                libasio-dev \
                libboost-dev 2>/dev/null || print_warning "Some packages may not be installed"
            
            sudo apt-get autoremove -y
            sudo apt-get autoclean
            
            print_success "System packages removed"
        else
            print_warning "System packages removal cancelled"
        fi
    else
        print_warning "apt-get not found. Please remove packages manually."
    fi
else
    print_info "Skipping system packages removal"
fi

# Remove environment variables
if [ $REMOVE_ENV_VARS -eq 1 ]; then
    print_info "Removing environment variables from ~/.bashrc..."
    
    if [ -f ~/.bashrc ]; then
        # Create backup
        cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)
        
        # Remove DDS Project Environment section
        sed -i '/# DDS Project Environment/,/^$/d' ~/.bashrc
        
        print_success "Environment variables removed"
        print_info "Backup created: ~/.bashrc.backup.*"
        echo ""
        echo "To apply changes, run: source ~/.bashrc"
        echo "Or restart your terminal"
    else
        print_warning "~/.bashrc not found"
    fi
else
    print_info "Skipping environment variables removal"
fi

echo ""
echo "========================================"
echo "  Uninstall Complete"
echo "========================================"
echo ""

if [ $REMOVE_PROJECT -eq 0 ] && [ $REMOVE_PACKAGES -eq 0 ] && [ $REMOVE_ENV_VARS -eq 0 ]; then
    print_info "Nothing was removed. Exiting."
else
    print_success "Uninstall completed!"
    echo ""
    echo "Note:"
    echo "  - If you removed system packages, they may still be used by other projects"
    echo "  - If you kept the project directory, you can reinstall dependencies later"
    echo "  - Environment variables backup is saved in ~/.bashrc.backup.*"
fi

echo ""

exit 0

