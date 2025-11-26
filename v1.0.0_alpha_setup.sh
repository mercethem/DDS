#!/bin/bash
# DDS Project - Complete Installation and Setup Script v1.0.0_alpha
# This script performs complete installation and setup:
# 1. Installs all system dependencies
# 2. Configures environment variables
# 3. Runs complete project setup
# 4. Builds all components

set -e

# Get script directory and project root dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Walk up to find project root (contains IDL and scenarios)
CURRENT_DIR="$SCRIPT_DIR"
while [ "$CURRENT_DIR" != "/" ] && [ "$CURRENT_DIR" != "." ]; do
    if [ -d "$CURRENT_DIR/IDL" ] && [ -d "$CURRENT_DIR/scenarios" ]; then
        PROJECT_ROOT="$CURRENT_DIR"
        break
    fi
    CURRENT_DIR="$(dirname "$CURRENT_DIR")"
done

cd "$PROJECT_ROOT"

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
    echo "  DDS Project Installation Script"
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

print_step() {
    echo -e "${CYAN}${BOLD}"
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo -e "${NC}"
}

# Root check
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root!"
   echo "Please run as normal user (sudo will be asked automatically when needed)"
   exit 1
fi

# Print banner
print_banner

echo "This script will:"
echo "  1. Install all system dependencies (requires sudo)"
echo "  2. Configure environment variables"
echo "  3. Run complete project setup"
echo "  4. Build all components"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# ========================================
# PHASE 1: Dependency Installation
# ========================================
print_step "PHASE 1: Installing System Dependencies"

INSTALL_SCRIPT="$PROJECT_ROOT/init/sh/install_system_dependencies.sh"

if [ ! -f "$INSTALL_SCRIPT" ]; then
    print_error "install_system_dependencies.sh not found: $INSTALL_SCRIPT"
    exit 1
fi

# Make script executable
chmod +x "$INSTALL_SCRIPT"

print_info "Running dependency installer..."
# Run installer non-interactively (bypass final "Press Enter" prompt)
if echo "" | bash "$INSTALL_SCRIPT"; then
    print_success "Dependencies installed successfully"
else
    print_error "Dependency installation failed!"
    exit 1
fi

echo ""

# ========================================
# PHASE 2: Environment Setup
# ========================================
print_step "PHASE 2: Setting Up Environment"

# Source bashrc to get new environment variables
print_info "Loading environment variables..."
if [ -f ~/.bashrc ]; then
    # Source bashrc in a subshell to get environment variables
    source ~/.bashrc 2>/dev/null || true
    
    # Export JAVA_HOME if it was added to bashrc
    if grep -q "JAVA_HOME" ~/.bashrc; then
        JAVA_HOME_PATH=$(grep "export JAVA_HOME" ~/.bashrc | head -1 | sed 's/.*export JAVA_HOME=\(.*\)/\1/' | tr -d '"' | tr -d "'")
        if [ -n "$JAVA_HOME_PATH" ]; then
            export JAVA_HOME="$JAVA_HOME_PATH"
            export PATH="$PATH:$JAVA_HOME/bin"
        fi
    fi
    
    # Export other environment variables
    export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-}
    export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:${PKG_CONFIG_PATH:-}
    export FASTDDS_HOME=/usr/local
fi

# Verify critical tools
print_info "Verifying installation..."

MISSING_TOOLS=()

if ! command -v cmake &> /dev/null; then
    MISSING_TOOLS+=("cmake")
fi

if ! command -v g++ &> /dev/null && ! command -v clang++ &> /dev/null; then
    MISSING_TOOLS+=("c++ compiler")
fi

if ! command -v python3 &> /dev/null; then
    MISSING_TOOLS+=("python3")
fi

if ! command -v java &> /dev/null; then
    MISSING_TOOLS+=("java")
fi

if ! command -v fastddsgen &> /dev/null; then
    MISSING_TOOLS+=("fastddsgen")
fi

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    print_warning "Some tools are missing: ${MISSING_TOOLS[*]}"
    print_warning "Please ensure all dependencies are installed correctly"
    read -p "Press Enter to continue anyway or Ctrl+C to cancel..."
else
    print_success "All critical tools are available"
fi

echo ""

# ========================================
# PHASE 3: Project Setup
# ========================================
print_step "PHASE 3: Running Project Setup"

SETUP_SCRIPT="$PROJECT_ROOT/init/sh/project_setup.sh"

if [ ! -f "$SETUP_SCRIPT" ]; then
    print_error "project_setup.sh not found: $SETUP_SCRIPT"
    exit 1
fi

# Make script executable
chmod +x "$SETUP_SCRIPT"

print_info "Running project setup..."
if bash "$SETUP_SCRIPT"; then
    print_success "Project setup completed successfully"
else
    print_error "Project setup failed!"
    exit 1
fi

echo ""

# ========================================
# PHASE 4: Final Verification
# ========================================
print_step "PHASE 4: Final Verification"

VERIFICATION_FAILED=0

# Check for generated code
print_info "Checking generated code..."
if [ -d "$PROJECT_ROOT/IDL" ] && [ -n "$(find "$PROJECT_ROOT/IDL" -maxdepth 1 -name "*_idl_generated" -type d 2>/dev/null)" ]; then
    print_success "IDL code generated"
else
    print_warning "No IDL generated code found"
    VERIFICATION_FAILED=1
fi

# Check for certificates
print_info "Checking certificates..."
CA_CERT="$PROJECT_ROOT/secure_dds/CA/mainca_cert.pem"
PC_NAME=$(hostname)
PC_CERT="$PROJECT_ROOT/secure_dds/participants/$PC_NAME/${PC_NAME}_cert.pem"

if [ -f "$CA_CERT" ] && [ -f "$PC_CERT" ]; then
    print_success "Certificates exist"
else
    print_warning "Certificates not found"
    VERIFICATION_FAILED=1
fi

# Check for built executables
print_info "Checking built executables..."
BUILT_COUNT=0
TOTAL_COUNT=0

for idl_dir in "$PROJECT_ROOT/IDL"/*_idl_generated; do
    if [ -d "$idl_dir" ]; then
        MODULE_NAME=$(basename "$idl_dir" | sed 's/_idl_generated//')
        MAIN_BINARY="$idl_dir/build/${MODULE_NAME}main"
        
        TOTAL_COUNT=$((TOTAL_COUNT + 1))
        
        if [ -f "$MAIN_BINARY" ] && [ -x "$MAIN_BINARY" ]; then
            BUILT_COUNT=$((BUILT_COUNT + 1))
        fi
    fi
done

if [ $BUILT_COUNT -eq $TOTAL_COUNT ] && [ $TOTAL_COUNT -gt 0 ]; then
    print_success "All IDL modules built ($BUILT_COUNT/$TOTAL_COUNT)"
else
    print_warning "Some modules not built ($BUILT_COUNT/$TOTAL_COUNT)"
    VERIFICATION_FAILED=1
fi

# Check monitoring executable
print_info "Checking monitoring application..."
MONITOR_EXE="$PROJECT_ROOT/monitoring/build/monitor"
if [ -f "$MONITOR_EXE" ] && [ -x "$MONITOR_EXE" ]; then
    print_success "Monitoring application built"
else
    print_warning "Monitoring application not found"
    VERIFICATION_FAILED=1
fi

echo ""

# ========================================
# Completion
# ========================================
print_step "Installation Complete!"

if [ $VERIFICATION_FAILED -eq 0 ]; then
    print_success "All components verified successfully!"
else
    print_warning "Some components may need attention (see warnings above)"
fi

echo ""
echo "Next steps:"
echo "  1. Restart your terminal or run: source ~/.bashrc"
echo "  2. Run tests and demo: bash v1.0.0_alpha_run.sh"
echo "  3. Test publishers: IDL/<MODULE>_idl_generated/build/<MODULE>main publisher"
echo "  4. Test subscribers: IDL/<MODULE>_idl_generated/build/<MODULE>main subscriber"
echo "  5. Run monitoring: monitoring/build/monitor"
echo "  6. Start demo dashboard: cd demo/run_demo && bash run_demo.sh"
echo ""
echo "Example commands:"
echo "  bash v1.0.0_alpha_run.sh"
echo "  IDL/Messaging_idl_generated/build/Messagingmain publisher"
echo "  IDL/CoreData_idl_generated/build/CoreDatamain subscriber"
echo "  monitoring/build/monitor \"0,1,2\""
echo ""

exit 0

