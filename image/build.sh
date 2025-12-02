#!/bin/bash
# DDS Project - Complete AppImage Builder
# This single script does everything: installs appimagetool and builds the AppImage
# Version: v1.0.0_beta

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_DIR="$SCRIPT_DIR"
PROJECT_ROOT="$(dirname "$IMAGE_DIR")"

cd "$IMAGE_DIR"

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
    echo "  DDS Project - Complete AppImage Builder"
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

# ========================================
# STEP 1: Install/Setup appimagetool
# ========================================
echo "========================================"
echo "STEP 1: Setting up appimagetool"
echo "========================================"
echo ""

APPIMAGETOOL=""

# Check if appimagetool is already installed
if command -v appimagetool &> /dev/null; then
    print_success "appimagetool is already installed"
    APPIMAGETOOL="appimagetool"
    appimagetool --version
else
    print_info "appimagetool not found, installing..."
    
    # Try to install FUSE (optional, for direct AppImage execution)
    # Prefer FUSE3, fallback to FUSE2
    FUSE_INSTALLED=0
    if command -v apt-get &> /dev/null; then
        print_info "Checking for FUSE library..."
        
        # Check if FUSE3 is already installed
        if ldconfig -p 2>/dev/null | grep -q libfuse3 || [ -f "/usr/lib/x86_64-linux-gnu/libfuse3.so" ] || [ -f "/usr/local/lib/libfuse3.so" ]; then
            print_success "FUSE3 is already installed"
            FUSE_INSTALLED=1
        # Check if FUSE2 is already installed
        elif ldconfig -p 2>/dev/null | grep -q libfuse2 || [ -f "/usr/lib/x86_64-linux-gnu/libfuse.so.2" ] || [ -f "/usr/local/lib/libfuse.so.2" ]; then
            print_success "FUSE2 is already installed"
            FUSE_INSTALLED=1
        else
            # Try to install FUSE3 first (preferred)
            print_info "Installing FUSE3 library (preferred)..."
            # Try different FUSE3 package names for different distributions
            if sudo apt-get update > /dev/null 2>&1; then
                if sudo apt-get install -y libfuse3-3 fuse3 2>/dev/null || \
                   sudo apt-get install -y libfuse3 fuse3 2>/dev/null || \
                   sudo apt-get install -y libfuse3-tools fuse3 2>/dev/null; then
                    print_success "FUSE3 installed successfully"
                    FUSE_INSTALLED=1
                else
                    # Fallback to FUSE2
                    print_info "FUSE3 not available, trying FUSE2..."
                    if sudo apt-get install -y libfuse2 2>/dev/null; then
                        print_success "FUSE2 installed successfully"
                        FUSE_INSTALLED=1
                    else
                        print_warning "FUSE installation skipped (will extract instead)"
                    fi
                fi
            else
                print_warning "Cannot update package list (will extract instead)"
            fi
        fi
    fi
    
    # Download appimagetool if not exists
    if [ ! -f "appimagetool-x86_64.AppImage" ]; then
        print_info "Downloading appimagetool..."
        wget -q --show-progress https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
        chmod +x appimagetool-x86_64.AppImage
        print_success "appimagetool downloaded"
    fi
    
    # Try to use AppImage directly (if FUSE is available - FUSE3 or FUSE2)
    if ./appimagetool-x86_64.AppImage --version > /dev/null 2>&1; then
        APPIMAGETOOL="./appimagetool-x86_64.AppImage"
        if [ $FUSE_INSTALLED -eq 1 ]; then
            # Check which FUSE version is being used
            if ldconfig -p 2>/dev/null | grep -q libfuse3 || [ -f "/usr/lib/x86_64-linux-gnu/libfuse3.so" ] || [ -f "/usr/local/lib/libfuse3.so" ]; then
                print_success "Using appimagetool AppImage directly (FUSE3)"
            else
                print_success "Using appimagetool AppImage directly (FUSE2)"
            fi
        else
            print_success "Using appimagetool AppImage directly"
        fi
    else
        # Extract and use binary directly (no FUSE needed)
        print_info "Extracting appimagetool (FUSE not required)..."
        ./appimagetool-x86_64.AppImage --appimage-extract > /dev/null 2>&1
        
        if [ -f "squashfs-root/AppRun" ]; then
            APPIMAGETOOL="./squashfs-root/AppRun"
            print_success "Using extracted appimagetool"
        else
            print_error "Failed to extract appimagetool"
            exit 1
        fi
    fi
fi

echo ""

# ========================================
# STEP 2: Create AppRun script
# ========================================
echo "========================================"
echo "STEP 2: Creating AppRun script"
echo "========================================"
echo ""

cat > AppRun << 'APPRUN_EOF'
#!/bin/bash
# AppRun - DDS Project Launcher for AppImage
# This script is executed when the AppImage is run
# The AppImage contains all project files and is completely self-contained

# Get AppImage directory (where AppRun is located)
APPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Project root is inside AppImage
APPIMAGE_PROJECT_ROOT="$APPDIR/usr/share/dds-project"

# Check if project files exist in AppImage
if [ ! -d "$APPIMAGE_PROJECT_ROOT" ] || [ ! -d "$APPIMAGE_PROJECT_ROOT/IDL" ]; then
    echo "========================================"
    echo "  DDS Project - Error"
    echo "========================================"
    echo ""
    echo "ERROR: Project files not found in AppImage!"
    echo ""
    echo "The AppImage appears to be corrupted or incomplete."
    echo "Please re-download from GitHub releases."
    echo ""
    exit 1
fi

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
    echo "  DDS Project - Launcher"
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

# Create a working directory in user's home for runtime files
# This allows the AppImage to work from anywhere
WORK_DIR="$HOME/.dds-project-runtime"
mkdir -p "$WORK_DIR"

# Copy project files to working directory (if not already there or if AppImage is newer)
if [ ! -d "$WORK_DIR/IDL" ] || [ "$APPIMAGE_PROJECT_ROOT" -nt "$WORK_DIR" ]; then
    print_info "Setting up working directory..."
    cp -r "$APPIMAGE_PROJECT_ROOT"/* "$WORK_DIR/" 2>/dev/null || true
fi

# Use working directory as project root
PROJECT_ROOT="$WORK_DIR"
cd "$PROJECT_ROOT"

# Print banner
print_banner

print_info "AppImage is self-contained - no external project directory needed"
print_info "Working directory: $WORK_DIR"
echo ""

# Check and install FUSE2 first (required for AppImage execution)
print_info "Checking FUSE2 library (required for AppImage)..."
echo ""

FUSE2_INSTALLED=0

# Check if FUSE2 is already installed
if ldconfig -p 2>/dev/null | grep -q libfuse.so.2 || \
   [ -f "/usr/lib/x86_64-linux-gnu/libfuse.so.2" ] || \
   [ -f "/usr/local/lib/libfuse.so.2" ] || \
   [ -f "/lib/x86_64-linux-gnu/libfuse.so.2" ]; then
    print_success "FUSE2 is already installed"
    FUSE2_INSTALLED=1
else
    # Try to install FUSE2
    if command -v apt-get &> /dev/null; then
        print_info "FUSE2 not found, installing libfuse2..."
        echo ""
        if sudo apt-get update > /dev/null 2>&1 && sudo apt-get install -y libfuse2 2>/dev/null; then
            # Verify installation
            if ldconfig -p 2>/dev/null | grep -q libfuse.so.2 || \
               [ -f "/usr/lib/x86_64-linux-gnu/libfuse.so.2" ] || \
               [ -f "/usr/local/lib/libfuse.so.2" ] || \
               [ -f "/lib/x86_64-linux-gnu/libfuse.so.2" ]; then
                print_success "FUSE2 installed successfully"
                FUSE2_INSTALLED=1
                # Update library cache
                sudo ldconfig 2>/dev/null || true
            else
                print_warning "FUSE2 package installed but library not found"
            fi
        else
            echo ""
            print_error "========================================"
            print_error "FUSE2 installation failed!"
            print_error "========================================"
            echo ""
            print_warning "FUSE2 is required for AppImage to run properly."
            echo ""
            print_info "To install FUSE2 manually, run:"
            echo "  sudo apt-get update"
            echo "  sudo apt-get install -y libfuse2"
            echo ""
            print_info "After installing FUSE2, run this AppImage again."
            echo ""
            print_warning "Continuing anyway, but AppImage may not work properly without FUSE2."
            echo ""
        fi
    else
        print_warning "apt-get not found, cannot install FUSE2 automatically"
        echo ""
        print_warning "AppImage requires FUSE2 to run. Please install it manually."
        echo ""
    fi
fi

echo ""

# ========================================
# PHASE 1: JavaScript/Node.js Installation (PRIORITY)
# ========================================
print_info "========================================"
print_info "PHASE 1: JavaScript/Node.js Setup"
print_info "========================================"
echo ""

# Install Node.js if not already installed
NODEJS_INSTALLED=0
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
    print_success "Node.js is already installed: $NODE_VERSION"
    NODEJS_INSTALLED=1
elif command -v nodejs &> /dev/null; then
    NODE_VERSION=$(nodejs --version 2>/dev/null || echo "unknown")
    print_success "Node.js is already installed (as nodejs): $NODE_VERSION"
    NODEJS_INSTALLED=1
fi

if [ $NODEJS_INSTALLED -eq 0 ]; then
    print_info "Node.js not found, installing..."
    echo ""
    
    NODEJS_INSTALL_ATTEMPTED=0
    
    if command -v apt-get &> /dev/null; then
        # First, ensure curl is available for NodeSource installation
        if ! command -v curl &> /dev/null; then
            print_info "Installing curl (required for Node.js installation)..."
            if sudo apt-get update > /dev/null 2>&1 && sudo apt-get install -y curl 2>/dev/null; then
                print_success "curl installed successfully"
            else
                print_warning "Failed to install curl, will try Ubuntu repositories for Node.js"
            fi
        fi
        
        # Try to install Node.js from Ubuntu repositories first
        print_info "Attempting to install Node.js from Ubuntu repositories..."
        if sudo apt-get update > /dev/null 2>&1 && sudo apt-get install -y nodejs npm 2>/dev/null; then
            # Verify installation
            if command -v node &> /dev/null && command -v npm &> /dev/null; then
                NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
                NPM_VERSION=$(npm --version 2>/dev/null || echo "unknown")
                print_success "Node.js installed from Ubuntu repositories"
                print_success "Node.js version: $NODE_VERSION"
                print_success "npm version: $NPM_VERSION"
                NODEJS_INSTALLED=1
                NODEJS_INSTALL_ATTEMPTED=1
            else
                print_warning "Node.js package installed but 'node' or 'npm' command not found"
            fi
        else
            print_warning "Failed to install Node.js from Ubuntu repositories"
        fi
        
        # Fallback: Install Node.js using NodeSource repository (recommended)
        if [ $NODEJS_INSTALLED -eq 0 ] && command -v curl &> /dev/null; then
            print_info "Attempting to install Node.js from NodeSource repository (recommended)..."
            if curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - > /dev/null 2>&1; then
                if sudo apt-get install -y nodejs 2>/dev/null; then
                    # Verify installation
                    if command -v node &> /dev/null && command -v npm &> /dev/null; then
                        NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
                        NPM_VERSION=$(npm --version 2>/dev/null || echo "unknown")
                        print_success "Node.js installed from NodeSource repository"
                        print_success "Node.js version: $NODE_VERSION"
                        print_success "npm version: $NPM_VERSION"
                        NODEJS_INSTALLED=1
                        NODEJS_INSTALL_ATTEMPTED=1
                    else
                        print_warning "Node.js package installed but 'node' or 'npm' command not found"
                    fi
                else
                    print_error "Failed to install Node.js from NodeSource repository"
                fi
            else
                print_error "Failed to setup NodeSource repository"
            fi
        elif [ $NODEJS_INSTALLED -eq 0 ] && ! command -v curl &> /dev/null; then
            print_error "curl not found, cannot install Node.js from NodeSource"
            print_info "Please install curl manually: sudo apt-get install curl"
        fi
    else
        print_error "apt-get not found, cannot install Node.js automatically"
    fi
    
    if [ $NODEJS_INSTALLED -eq 0 ]; then
        echo ""
        print_error "========================================"
        print_error "Node.js installation failed!"
        print_error "========================================"
        echo ""
        print_warning "Node.js is required for the demo dashboard to work."
        print_warning "The system will continue but demo features will be unavailable."
        echo ""
        print_info "To install Node.js manually, run:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install -y curl"
        echo "  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
        echo "  sudo apt-get install -y nodejs"
        echo ""
        print_info "Or try Ubuntu repositories:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install -y nodejs npm"
        echo ""
        print_info "After installing Node.js, run this AppImage again."
        echo ""
    fi
fi

echo ""

# Install demo npm packages (JavaScript dependencies)
if [ $NODEJS_INSTALLED -eq 1 ]; then
    print_info "Installing demo dashboard npm packages..."
    DEMO_DIR="$PROJECT_ROOT/demo"
    DEMO_PACKAGE_JSON="$DEMO_DIR/package.json"
    
    if [ -f "$DEMO_PACKAGE_JSON" ]; then
        cd "$DEMO_DIR"
        if npm install; then
            print_success "Demo dashboard dependencies installed successfully"
        else
            print_error "Failed to install demo dashboard dependencies"
        fi
        cd "$PROJECT_ROOT"
    else
        print_warning "package.json not found at $DEMO_PACKAGE_JSON"
    fi
else
    print_warning "Skipping npm packages installation (Node.js not available)"
fi

echo ""

# ========================================
# PHASE 2: System Dependencies Installation
# ========================================
print_info "========================================"
print_info "PHASE 2: System Dependencies"
print_info "========================================"
echo ""

DEPENDENCIES_SCRIPT="$PROJECT_ROOT/init/sh/install_system_dependencies.sh"

if [ -f "$DEPENDENCIES_SCRIPT" ]; then
    chmod +x "$DEPENDENCIES_SCRIPT"
    if bash "$DEPENDENCIES_SCRIPT"; then
        print_success "System dependencies installation completed"
        echo ""
        # Reload environment
        if [ -f ~/.bashrc ]; then
            source ~/.bashrc 2>/dev/null || true
        fi
    else
        print_error "System dependencies installation failed!"
        echo ""
        print_warning "Continuing anyway, but some features may not work..."
        echo ""
    fi
else
    print_error "install_system_dependencies.sh not found: $DEPENDENCIES_SCRIPT"
    echo ""
    print_warning "Continuing anyway, but some features may not work..."
    echo ""
fi

# ========================================
# PHASE 3: Fast-DDS and Monitoring Build
# ========================================
print_info "========================================"
print_info "PHASE 3: Fast-DDS and Monitoring Build"
print_info "========================================"
echo ""

# Run Fast-DDS auto installation script
print_info "Running Fast-DDS Auto Installation..."
echo ""
FASTDDS_SCRIPT="$PROJECT_ROOT/init/sh/fastdds_and_npm_auto_install.sh"
if [ -f "$FASTDDS_SCRIPT" ]; then
    chmod +x "$FASTDDS_SCRIPT"
    if bash "$FASTDDS_SCRIPT"; then
        print_success "Fast-DDS installation completed"
    else
        print_warning "Fast-DDS installation failed (continuing anyway...)"
    fi
else
    print_warning "fastdds_and_npm_auto_install.sh not found: $FASTDDS_SCRIPT"
fi
echo ""

# Clean monitoring build directory and rebuild
print_info "Cleaning and Building Monitoring Application..."
echo ""
MONITORING_BUILD_DIR="$PROJECT_ROOT/monitoring/build"
MONITORING_BUILD_SCRIPT="$PROJECT_ROOT/monitoring/build_monitoring/build_monitoring.sh"

if [ -d "$MONITORING_BUILD_DIR" ]; then
    print_info "Removing existing monitoring build directory..."
    rm -rf "$MONITORING_BUILD_DIR"
    print_success "Monitoring build directory removed."
else
    print_info "No existing monitoring build directory found."
fi

if [ -f "$MONITORING_BUILD_SCRIPT" ]; then
    chmod +x "$MONITORING_BUILD_SCRIPT"
    if bash "$MONITORING_BUILD_SCRIPT"; then
        print_success "Monitoring application built successfully"
    else
        print_error "Monitoring build failed!"
    fi
else
    print_warning "build_monitoring.sh not found at $MONITORING_BUILD_SCRIPT"
fi
echo ""

# Reload environment after Fast-DDS installation
if [ -f ~/.bashrc ]; then
    source ~/.bashrc 2>/dev/null || true
fi
sudo ldconfig 2>/dev/null || true

# ========================================
# PHASE 4: System Readiness Check
# ========================================
print_info "========================================"
print_info "PHASE 4: System Readiness Check"
print_info "========================================"
echo ""

SYSTEM_READY=1
MISSING_COMPONENTS=()

# Check essential build tools (required for compilation)
if ! command -v cmake &> /dev/null; then
    SYSTEM_READY=0
    MISSING_COMPONENTS+=("CMake")
fi

if ! command -v gcc &> /dev/null && ! command -v g++ &> /dev/null; then
    SYSTEM_READY=0
    MISSING_COMPONENTS+=("GCC/G++ compiler")
fi

if ! command -v python3 &> /dev/null; then
    SYSTEM_READY=0
    MISSING_COMPONENTS+=("Python3")
fi

if ! command -v java &> /dev/null && [ -z "$JAVA_HOME" ]; then
    SYSTEM_READY=0
    MISSING_COMPONENTS+=("Java (JDK)")
fi

# Check Node.js (required for demo)
if [ $NODEJS_INSTALLED -eq 0 ]; then
    SYSTEM_READY=0
    MISSING_COMPONENTS+=("Node.js")
fi

# Check npm packages
if [ $NODEJS_INSTALLED -eq 1 ]; then
    DEMO_DIR="$PROJECT_ROOT/demo"
    if [ ! -d "$DEMO_DIR/node_modules" ]; then
        SYSTEM_READY=0
        MISSING_COMPONENTS+=("Demo npm packages")
    fi
fi

# Check Fast-DDS installation
if ! command -v fastddsgen &> /dev/null && [ ! -f "/usr/local/bin/fastddsgen" ]; then
    SYSTEM_READY=0
    MISSING_COMPONENTS+=("Fast-DDS")
fi

# Check for IDL generated directories
if [ ! -d "$PROJECT_ROOT/IDL" ] || [ -z "$(find "$PROJECT_ROOT/IDL" -maxdepth 1 -name "*_idl_generated" -type d 2>/dev/null)" ]; then
    SYSTEM_READY=0
    MISSING_COMPONENTS+=("IDL generated modules")
fi

# Check for built executables in IDL modules
IDL_EXECUTABLES_FOUND=0
for idl_dir in "$PROJECT_ROOT/IDL"/*_idl_generated; do
    if [ -d "$idl_dir" ]; then
        MODULE_NAME=$(basename "$idl_dir" | sed 's/_idl_generated//')
        MAIN_BINARY="$idl_dir/build/${MODULE_NAME}main"
        
        # Try build/ first, then root
        if [ ! -f "$MAIN_BINARY" ]; then
            MAIN_BINARY="$idl_dir/${MODULE_NAME}main"
        fi
        
        if [ -f "$MAIN_BINARY" ] && [ -x "$MAIN_BINARY" ]; then
            IDL_EXECUTABLES_FOUND=$((IDL_EXECUTABLES_FOUND + 1))
        fi
    fi
done

if [ $IDL_EXECUTABLES_FOUND -eq 0 ]; then
    SYSTEM_READY=0
    MISSING_COMPONENTS+=("IDL module executables")
fi

# Check for monitoring executable
if [ ! -f "$PROJECT_ROOT/monitoring/build/monitor" ] || [ ! -x "$PROJECT_ROOT/monitoring/build/monitor" ]; then
    SYSTEM_READY=0
    MISSING_COMPONENTS+=("Monitoring executable")
fi

# Check for certificates
CA_CERT="$PROJECT_ROOT/secure_dds/CA/mainca_cert.pem"
PC_NAME=$(hostname)
PC_CERT="$PROJECT_ROOT/secure_dds/participants/$PC_NAME/${PC_NAME}_cert.pem"

if [ ! -f "$CA_CERT" ] || [ ! -f "$PC_CERT" ]; then
    SYSTEM_READY=0
    MISSING_COMPONENTS+=("Security certificates")
fi

# Display status
if [ $SYSTEM_READY -eq 1 ]; then
    print_success "All system components are ready"
    echo ""
else
    echo ""
    print_warning "========================================"
    print_warning "System is not ready. Missing components:"
    print_warning "========================================"
    echo ""
    for component in "${MISSING_COMPONENTS[@]}"; do
        echo "  ✗ $component"
    done
    echo ""
    
    # Check if Node.js is missing and provide specific guidance
    if [[ " ${MISSING_COMPONENTS[@]} " =~ " Node.js " ]]; then
        print_info "Node.js installation may have failed during setup."
        print_info "This is common on first run. Please try running the AppImage again."
        echo ""
    fi
    
    # Run setup to fix missing components
    print_info "Running project setup to install missing components..."
    echo ""
    
    SETUP_SCRIPT="$PROJECT_ROOT/init/sh/project_setup.sh"
    
    if [ ! -f "$SETUP_SCRIPT" ]; then
        print_error "Setup script not found: $SETUP_SCRIPT"
        echo ""
        exit 1
    fi
    
    # Make script executable
    chmod +x "$SETUP_SCRIPT"
    
    # Run setup
    if bash "$SETUP_SCRIPT"; then
        print_success "Setup completed successfully"
        echo ""
        
        # Re-check system readiness after setup
        SYSTEM_READY=1
        MISSING_COMPONENTS=()
        
        # Re-check all components
        # Check essential build tools
        if ! command -v cmake &> /dev/null; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("CMake")
        fi
        
        if ! command -v gcc &> /dev/null && ! command -v g++ &> /dev/null; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("GCC/G++ compiler")
        fi
        
        if ! command -v python3 &> /dev/null; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("Python3")
        fi
        
        if ! command -v java &> /dev/null && [ -z "$JAVA_HOME" ]; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("Java (JDK)")
        fi
        
        # Check Node.js
        if [ $NODEJS_INSTALLED -eq 0 ]; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("Node.js")
        fi
        
        # Check npm packages
        if [ ! -d "$PROJECT_ROOT/demo/node_modules" ] && [ $NODEJS_INSTALLED -eq 1 ]; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("Demo npm packages")
        fi
        
        # Check Fast-DDS
        if ! command -v fastddsgen &> /dev/null && [ ! -f "/usr/local/bin/fastddsgen" ]; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("Fast-DDS")
        fi
        
        # Check IDL modules
        if [ -z "$(find "$PROJECT_ROOT/IDL" -maxdepth 1 -name "*_idl_generated" -type d 2>/dev/null)" ]; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("IDL generated modules")
        fi
        
        # Check IDL executables
        IDL_EXECUTABLES_FOUND=0
        for idl_dir in "$PROJECT_ROOT/IDL"/*_idl_generated; do
            if [ -d "$idl_dir" ]; then
                MODULE_NAME=$(basename "$idl_dir" | sed 's/_idl_generated//')
                MAIN_BINARY="$idl_dir/build/${MODULE_NAME}main"
                if [ ! -f "$MAIN_BINARY" ]; then
                    MAIN_BINARY="$idl_dir/${MODULE_NAME}main"
                fi
                if [ -f "$MAIN_BINARY" ] && [ -x "$MAIN_BINARY" ]; then
                    IDL_EXECUTABLES_FOUND=$((IDL_EXECUTABLES_FOUND + 1))
                fi
            fi
        done
        
        if [ $IDL_EXECUTABLES_FOUND -eq 0 ]; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("IDL module executables")
        fi
        
        # Check monitoring executable
        if [ ! -f "$PROJECT_ROOT/monitoring/build/monitor" ] || [ ! -x "$PROJECT_ROOT/monitoring/build/monitor" ]; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("Monitoring executable")
        fi
        
        # Check certificates
        if [ ! -f "$CA_CERT" ] || [ ! -f "$PC_CERT" ]; then
            SYSTEM_READY=0
            MISSING_COMPONENTS+=("Security certificates")
        fi
    else
        print_error "Setup failed!"
        echo ""
        exit 1
    fi
fi

# ========================================
# PHASE 5: Start Tests and Demo (Only if system is ready)
# ========================================
if [ $SYSTEM_READY -eq 1 ]; then
    print_info "========================================"
    print_info "PHASE 5: Starting Tests and Demo"
    print_info "========================================"
    echo ""
    
    RUN_SCRIPT="$PROJECT_ROOT/init/sh/run_tests_and_demo.sh"
    
    if [ ! -f "$RUN_SCRIPT" ]; then
        print_error "Run script not found: $RUN_SCRIPT"
        echo ""
        exit 1
    fi
    
    # Make script executable
    chmod +x "$RUN_SCRIPT"
    
    # Run tests and demo
    bash "$RUN_SCRIPT"
else
    echo ""
    print_error "========================================"
    print_error "System is not ready. Cannot start tests and demo."
    print_error "========================================"
    echo ""
    print_warning "Missing components:"
    for component in "${MISSING_COMPONENTS[@]}"; do
        echo "  ✗ $component"
    done
    echo ""
    
    # Provide specific guidance based on missing components
    if [[ " ${MISSING_COMPONENTS[@]} " =~ " Node.js " ]]; then
        print_info "========================================"
        print_info "Node.js Installation Guide"
        print_info "========================================"
        echo ""
        print_info "Node.js installation may have failed. This is common on first run."
        echo ""
        print_info "Option 1: Run this AppImage again (recommended)"
        print_info "  The installation will be retried automatically."
        echo ""
        print_info "Option 2: Install Node.js manually"
        print_info "  sudo apt-get update"
        print_info "  sudo apt-get install -y curl"
        print_info "  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
        print_info "  sudo apt-get install -y nodejs"
        echo ""
    fi
    
    if [[ " ${MISSING_COMPONENTS[@]} " =~ " FUSE2 " ]]; then
        print_info "========================================"
        print_info "FUSE2 Installation Guide"
        print_info "========================================"
        echo ""
        print_info "Install FUSE2 manually:"
        print_info "  sudo apt-get update"
        print_info "  sudo apt-get install -y libfuse2"
        echo ""
    fi
    
    print_info "After fixing the missing components, run this AppImage again."
    echo ""
    exit 1
fi

exit 0
APPRUN_EOF

chmod +x AppRun
print_success "AppRun script created"

echo ""

# ========================================
# STEP 3: Create desktop entry
# ========================================
echo "========================================"
echo "STEP 3: Creating desktop entry"
echo "========================================"
echo ""

cat > dds-project.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Name=DDS Project
Comment=Data Distribution Service Project - Run Tests and Demo
Exec=dds-project.AppImage
Icon=dds-project
Terminal=true
Type=Application
Categories=Development;
StartupNotify=true
MimeType=
DESKTOP_EOF

print_success "Desktop entry created"

echo ""

# ========================================
# STEP 4: Create icon (if not exists)
# ========================================
echo "========================================"
echo "STEP 4: Creating icon"
echo "========================================"
echo ""

if [ ! -f "dds-project.png" ]; then
    print_info "Creating icon..."
    # Try to create icon using Python PIL
    python3 << 'ICON_EOF' 2>/dev/null || print_warning "Icon creation skipped (PIL not available)"
from PIL import Image, ImageDraw, ImageFont
import os

# Create 256x256 image
img = Image.new('RGB', (256, 256), color='#4A90E2')
d = ImageDraw.Draw(img)

# Draw circle
d.ellipse([30, 30, 226, 226], fill='white', outline='#4A90E2', width=4)

# Draw text
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
except:
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()

text = "DDS"
bbox = d.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
position = ((256 - text_width) // 2, (256 - text_height) // 2 - 10)
d.text(position, text, fill='#4A90E2', font=font)

img.save('dds-project.png')
print("Icon created successfully")
ICON_EOF
    
    if [ -f "dds-project.png" ]; then
        print_success "Icon created"
    else
        print_warning "Icon not created (will work without icon)"
    fi
else
    print_success "Icon already exists"
fi

echo ""

# ========================================
# STEP 5: Build AppImage
# ========================================
echo "========================================"
echo "STEP 5: Building AppImage"
echo "========================================"
echo ""

# Create AppDir structure
print_info "[1/6] Creating AppDir structure..."
rm -rf AppDir
mkdir -p AppDir
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/512x512/apps

# Copy AppRun
print_info "[2/6] Copying AppRun..."
cp AppRun AppDir/
chmod +x AppDir/AppRun

# Copy desktop entry
print_info "[3/6] Copying desktop entry..."
cp dds-project.desktop AppDir/
cp dds-project.desktop AppDir/usr/share/applications/

# Copy icon (if exists)
if [ -f "dds-project.png" ]; then
    print_info "[4/6] Copying icon..."
    cp dds-project.png AppDir/
    cp dds-project.png AppDir/usr/share/icons/hicolor/512x512/apps/
else
    print_warning "[4/6] Icon not found, skipping..."
fi

# Copy entire project into AppImage
print_info "[5/6] Copying project files into AppImage..."
mkdir -p AppDir/usr/share/dds-project

# Copy essential directories
if [ -d "$PROJECT_ROOT/IDL" ]; then
    cp -r "$PROJECT_ROOT/IDL" AppDir/usr/share/dds-project/
fi

if [ -d "$PROJECT_ROOT/scripts" ]; then
    cp -r "$PROJECT_ROOT/scripts" AppDir/usr/share/dds-project/
fi

if [ -d "$PROJECT_ROOT/scenarios" ]; then
    cp -r "$PROJECT_ROOT/scenarios" AppDir/usr/share/dds-project/
fi

if [ -d "$PROJECT_ROOT/init" ]; then
    cp -r "$PROJECT_ROOT/init" AppDir/usr/share/dds-project/
fi

if [ -d "$PROJECT_ROOT/monitoring" ]; then
    cp -r "$PROJECT_ROOT/monitoring" AppDir/usr/share/dds-project/
fi

if [ -d "$PROJECT_ROOT/demo" ]; then
    cp -r "$PROJECT_ROOT/demo" AppDir/usr/share/dds-project/
fi

if [ -d "$PROJECT_ROOT/include" ]; then
    cp -r "$PROJECT_ROOT/include" AppDir/usr/share/dds-project/
fi

# Note: v1.0.0_alpha_setup.sh and v1.0.0_alpha_run.sh were removed
# Their functionality is now integrated into AppRun and other modular scripts

# Create secure_dds directory structure (will be populated at runtime)
mkdir -p AppDir/usr/share/dds-project/secure_dds/CA/private
mkdir -p AppDir/usr/share/dds-project/secure_dds/participants

print_success "Project files copied"

# Build AppImage
print_info "[6/6] Building AppImage..."
# AppImage name
APPIMAGE_NAME="DDS-v1.0.0_beta-x86_64.AppImage"

# Remove old AppImage if exists
rm -f "$IMAGE_DIR/$APPIMAGE_NAME"
rm -f "$PROJECT_ROOT/$APPIMAGE_NAME"

# Build with appimagetool (specify architecture)
ARCH=x86_64 $APPIMAGETOOL AppDir "$APPIMAGE_NAME"

# Cleanup extracted files if used
if [ -d "squashfs-root" ]; then
    rm -rf squashfs-root
fi

# Move to image directory (if not already there)
if [ ! -f "$IMAGE_DIR/$APPIMAGE_NAME" ]; then
    mv "$APPIMAGE_NAME" "$IMAGE_DIR/"
fi

# Cleanup temporary files
rm -rf AppDir
rm -f AppRun dds-project.desktop

echo ""
echo "========================================"
echo "  Build Complete!"
echo "========================================"
echo ""
print_success "AppImage created: $IMAGE_DIR/$APPIMAGE_NAME"
echo ""
echo "The AppImage is completely self-contained!"
echo "It contains all project files and can run from anywhere."
echo ""
echo "To use:"
echo "  1. Copy the AppImage anywhere you want (Desktop, Downloads, etc.)"
echo "  2. Make it executable: chmod +x $APPIMAGE_NAME"
echo "  3. Double-click or run: ./$APPIMAGE_NAME"
echo ""
echo "The AppImage will:"
echo "  - Extract project files to ~/.dds-project-runtime on first run"
echo "  - Run setup automatically if needed"
echo "  - Start tests and demo automatically"
echo "  - Work completely independently (no external project directory needed)"
echo ""

exit 0

