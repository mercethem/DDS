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
    echo "  Version: v1.0.0_beta"
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
APPRUNTIME_EXISTS=0
NODEJS_INSTALLED=0
MANUAL_FASTDDS_EXISTS=0

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

# Check AppImage runtime directory
if [ -d ~/.dds-project-runtime ]; then
    APPRUNTIME_EXISTS=1
fi

# Check Node.js installation
if command -v node &> /dev/null; then
    NODEJS_INSTALLED=1
fi

# Check manual Fast-DDS installation (common locations)
if [ -f "/usr/local/lib/libfastdds.so" ] || \
   [ -d "/usr/local/include/fastdds" ] || \
   [ -d "/opt/fastdds" ] || \
   [ -f "/usr/local/bin/fastddsgen" ] || \
   [ -d "$HOME/fastdds" ] || \
   [ -d "$HOME/Fast-DDS" ]; then
    MANUAL_FASTDDS_EXISTS=1
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

if [ $APPRUNTIME_EXISTS -eq 1 ]; then
    echo "  ✓ AppImage runtime directory: ~/.dds-project-runtime"
else
    echo "  ✗ AppImage runtime directory not found"
fi

if [ $NODEJS_INSTALLED -eq 1 ]; then
    NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
    echo "  ✓ Node.js installed: $NODE_VERSION"
else
    echo "  ✗ Node.js not found"
fi

if [ $MANUAL_FASTDDS_EXISTS -eq 1 ]; then
    echo "  ✓ Manual Fast-DDS installation detected"
else
    echo "  ✗ Manual Fast-DDS installation not detected"
fi

echo ""

# Options
REMOVE_PROJECT=0
REMOVE_PACKAGES=0
REMOVE_ENV_VARS=0
REMOVE_APPRUNTIME=0
REMOVE_NODEJS=0
REMOVE_MANUAL_FASTDDS=0

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

# Ask about AppImage runtime directory
if [ $APPRUNTIME_EXISTS -eq 1 ]; then
    echo ""
    read -p "Remove AppImage runtime directory (~/.dds-project-runtime)? (y/N): " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        REMOVE_APPRUNTIME=1
    fi
fi

# Ask about Node.js
if [ $NODEJS_INSTALLED -eq 1 ]; then
    echo ""
    echo "⚠ WARNING: Removing Node.js may affect other projects!"
    read -p "Remove Node.js and npm? (y/N): " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        REMOVE_NODEJS=1
    fi
fi

# Ask about manual Fast-DDS
if [ $MANUAL_FASTDDS_EXISTS -eq 1 ]; then
    echo ""
    echo "⚠ WARNING: Manual Fast-DDS installation detected!"
    read -p "Remove manual Fast-DDS installation? (y/N): " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        REMOVE_MANUAL_FASTDDS=1
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

# Remove AppImage runtime directory
if [ $REMOVE_APPRUNTIME -eq 1 ]; then
    print_info "Removing AppImage runtime directory: ~/.dds-project-runtime"
    if [ -d ~/.dds-project-runtime ]; then
        rm -rf ~/.dds-project-runtime
        print_success "AppImage runtime directory removed"
    else
        print_warning "AppImage runtime directory not found"
    fi
else
    print_info "Skipping AppImage runtime directory removal"
fi

# Remove Node.js and npm
if [ $REMOVE_NODEJS -eq 1 ]; then
    print_info "Removing Node.js and npm..."
    
    if command -v apt-get &> /dev/null; then
        echo ""
        echo "The following packages will be removed:"
        echo "  - nodejs"
        echo "  - npm"
        echo ""
        read -p "Continue? (yes/NO): " confirm
        
        if [ "$confirm" = "yes" ]; then
            # Remove Node.js and npm packages
            sudo apt-get remove --purge -y nodejs npm 2>/dev/null || print_warning "Some packages may not be installed"
            
            # Remove NodeSource repository if added
            if [ -f /etc/apt/sources.list.d/nodesource.list ]; then
                sudo rm -f /etc/apt/sources.list.d/nodesource.list
                print_info "NodeSource repository removed"
            fi
            
            # Remove Node.js from common installation locations
            if [ -d /usr/local/lib/node_modules ]; then
                sudo rm -rf /usr/local/lib/node_modules
                print_info "Removed /usr/local/lib/node_modules"
            fi
            if [ -d /usr/local/include/node ]; then
                sudo rm -rf /usr/local/include/node
                print_info "Removed /usr/local/include/node"
            fi
            if [ -f /usr/local/bin/node ]; then
                sudo rm -f /usr/local/bin/node
                print_info "Removed /usr/local/bin/node"
            fi
            if [ -f /usr/local/bin/npm ]; then
                sudo rm -f /usr/local/bin/npm
                print_info "Removed /usr/local/bin/npm"
            fi
            if [ -f /usr/local/bin/npx ]; then
                sudo rm -f /usr/local/bin/npx
                print_info "Removed /usr/local/bin/npx"
            fi
            
            # Remove npm cache and config
            if [ -d ~/.npm ]; then
                rm -rf ~/.npm
                print_info "Removed ~/.npm"
            fi
            
            sudo apt-get autoremove -y
            print_success "Node.js and npm removed"
        else
            print_warning "Node.js removal cancelled"
        fi
    else
        print_warning "apt-get not found. Please remove Node.js manually."
    fi
else
    print_info "Skipping Node.js removal"
fi

# Remove manual Fast-DDS installation
if [ $REMOVE_MANUAL_FASTDDS -eq 1 ]; then
    print_info "Removing manual Fast-DDS installation..."
    
    echo ""
    echo "⚠ WARNING: This will remove manually installed Fast-DDS!"
    echo "The following locations will be checked and removed if found:"
    echo "  - /usr/local/lib/libfastdds*"
    echo "  - /usr/local/include/fastdds"
    echo "  - /opt/fastdds"
    echo "  - /usr/local/bin/fastddsgen"
    echo "  - ~/fastdds"
    echo "  - ~/Fast-DDS"
    echo ""
    read -p "Continue? (yes/NO): " confirm
    
    if [ "$confirm" = "yes" ]; then
        REMOVED_ANY=0
        
        # Remove from /usr/local/lib
        if ls /usr/local/lib/libfastdds* 2>/dev/null | grep -q .; then
            sudo rm -f /usr/local/lib/libfastdds*
            sudo rm -f /usr/local/lib/libfastcdr*
            print_info "Removed Fast-DDS libraries from /usr/local/lib"
            REMOVED_ANY=1
        fi
        
        # Remove from /usr/local/include
        if [ -d /usr/local/include/fastdds ]; then
            sudo rm -rf /usr/local/include/fastdds
            sudo rm -rf /usr/local/include/fastcdr
            print_info "Removed Fast-DDS headers from /usr/local/include"
            REMOVED_ANY=1
        fi
        
        # Remove from /opt/fastdds
        if [ -d /opt/fastdds ]; then
            sudo rm -rf /opt/fastdds
            print_info "Removed /opt/fastdds"
            REMOVED_ANY=1
        fi
        
        # Remove fastddsgen binary
        if [ -f /usr/local/bin/fastddsgen ]; then
            sudo rm -f /usr/local/bin/fastddsgen
            print_info "Removed /usr/local/bin/fastddsgen"
            REMOVED_ANY=1
        fi
        
        # Remove from home directory
        if [ -d ~/fastdds ]; then
            rm -rf ~/fastdds
            print_info "Removed ~/fastdds"
            REMOVED_ANY=1
        fi
        
        if [ -d ~/Fast-DDS ]; then
            rm -rf ~/Fast-DDS
            print_info "Removed ~/Fast-DDS"
            REMOVED_ANY=1
        fi
        
        # Update library cache
        if [ $REMOVED_ANY -eq 1 ]; then
            sudo ldconfig 2>/dev/null || true
            print_success "Manual Fast-DDS installation removed"
        else
            print_warning "No manual Fast-DDS installation found in common locations"
        fi
    else
        print_warning "Manual Fast-DDS removal cancelled"
    fi
else
    print_info "Skipping manual Fast-DDS removal"
fi

echo ""
echo "========================================"
echo "  Uninstall Complete"
echo "========================================"
echo ""

if [ $REMOVE_PROJECT -eq 0 ] && [ $REMOVE_PACKAGES -eq 0 ] && [ $REMOVE_ENV_VARS -eq 0 ] && \
   [ $REMOVE_APPRUNTIME -eq 0 ] && [ $REMOVE_NODEJS -eq 0 ] && [ $REMOVE_MANUAL_FASTDDS -eq 0 ]; then
    print_info "Nothing was removed. Exiting."
else
    print_success "Uninstall completed!"
    echo ""
    echo "Note:"
    echo "  - If you removed system packages, they may still be used by other projects"
    echo "  - If you kept the project directory, you can reinstall dependencies later"
    echo "  - Environment variables backup is saved in ~/.bashrc.backup.*"
    echo "  - AppImage file (DDS-v1.0.0_beta-x86_64.AppImage) must be removed manually if needed"
fi

echo ""

exit 0

