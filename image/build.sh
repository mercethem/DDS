#!/bin/bash
# DDS Project - Complete AppImage Builder
# This single script does everything: installs appimagetool and builds the AppImage
# Version: v1.0.0_alpha

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
    if command -v apt-get &> /dev/null; then
        print_info "Installing FUSE library (optional)..."
        sudo apt-get update > /dev/null 2>&1
        sudo apt-get install -y libfuse2 > /dev/null 2>&1 || print_warning "FUSE installation skipped (will extract instead)"
    fi
    
    # Download appimagetool if not exists
    if [ ! -f "appimagetool-x86_64.AppImage" ]; then
        print_info "Downloading appimagetool..."
        wget -q --show-progress https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
        chmod +x appimagetool-x86_64.AppImage
        print_success "appimagetool downloaded"
    fi
    
    # Try to use AppImage directly (if FUSE is available)
    if ./appimagetool-x86_64.AppImage --version > /dev/null 2>&1; then
        APPIMAGETOOL="./appimagetool-x86_64.AppImage"
        print_success "Using appimagetool AppImage directly"
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

# Check system dependencies first
print_info "Checking system dependencies..."

DEPENDENCIES_SCRIPT="$PROJECT_ROOT/init/sh/install_system_dependencies.sh"
DEPENDENCIES_NEEDED=0
MISSING_DEPS=()

# Check for essential build tools
if ! command -v cmake &> /dev/null; then
    DEPENDENCIES_NEEDED=1
    MISSING_DEPS+=("cmake")
fi

if ! command -v g++ &> /dev/null && ! command -v gcc &> /dev/null; then
    DEPENDENCIES_NEEDED=1
    MISSING_DEPS+=("gcc/g++")
fi

if ! command -v git &> /dev/null; then
    DEPENDENCIES_NEEDED=1
    MISSING_DEPS+=("git")
fi

if ! command -v pkg-config &> /dev/null; then
    DEPENDENCIES_NEEDED=1
    MISSING_DEPS+=("pkg-config")
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    DEPENDENCIES_NEEDED=1
    MISSING_DEPS+=("python3")
fi

# Check for Java
if ! command -v java &> /dev/null; then
    DEPENDENCIES_NEEDED=1
    MISSING_DEPS+=("java")
fi

# Check for essential libraries (development headers)
if [ ! -f "/usr/include/openssl/ssl.h" ] && [ ! -f "/usr/local/include/openssl/ssl.h" ]; then
    DEPENDENCIES_NEEDED=1
    MISSING_DEPS+=("libssl-dev")
fi

if [ ! -f "/usr/include/tinyxml2.h" ] && [ ! -f "/usr/local/include/tinyxml2.h" ]; then
    DEPENDENCIES_NEEDED=1
    MISSING_DEPS+=("libtinyxml2-dev")
fi

# Check for Fast-DDS libraries
FASTDDS_FOUND=0
if pkg-config --exists fastdds 2>/dev/null; then
    FASTDDS_FOUND=1
elif ldconfig -p 2>/dev/null | grep -q libfastdds; then
    FASTDDS_FOUND=1
elif [ -f "/usr/lib/x86_64-linux-gnu/libfastdds.so" ] || [ -f "/usr/local/lib/libfastdds.so" ]; then
    FASTDDS_FOUND=1
fi

if [ $FASTDDS_FOUND -eq 0 ]; then
    DEPENDENCIES_NEEDED=1
    MISSING_DEPS+=("Fast-DDS libraries")
fi

# Check for fastddsgen
if ! command -v fastddsgen &> /dev/null; then
    DEPENDENCIES_NEEDED=1
    MISSING_DEPS+=("fastddsgen")
fi

# Check post-install build requirements (Fast-DDS manual install and monitoring build)
POST_INSTALL_BUILD_NEEDED=0
POST_INSTALL_BUILD_SCRIPT="$PROJECT_ROOT/init/sh/post_install_build.sh"

# Check if Fast-DDS manual installation is done (fastdds_and_npm_auto_install.sh result)
FASTDDS_MANUAL_INSTALLED=0
if [ -d "$HOME/Fast-DDS-v3.2.2-Linux" ]; then
    FASTDDS_MANUAL_INSTALLED=1
fi

# Check if monitoring application is built
MONITORING_BUILT=0
if [ -f "$PROJECT_ROOT/monitoring/build/monitor" ] && [ -x "$PROJECT_ROOT/monitoring/build/monitor" ]; then
    MONITORING_BUILT=1
fi

# Determine if post-install build is needed
if [ $FASTDDS_MANUAL_INSTALLED -eq 0 ] || [ $MONITORING_BUILT -eq 0 ]; then
    POST_INSTALL_BUILD_NEEDED=1
fi

# Show missing dependencies if any
if [ $DEPENDENCIES_NEEDED -eq 1 ]; then
    print_warning "Missing dependencies detected:"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "  - $dep"
    done
fi

# If dependencies are needed, run install script
if [ $DEPENDENCIES_NEEDED -eq 1 ]; then
    print_warning "System dependencies are missing. Installing dependencies..."
    echo ""
    
    if [ -f "$DEPENDENCIES_SCRIPT" ]; then
        chmod +x "$DEPENDENCIES_SCRIPT"
        if bash "$DEPENDENCIES_SCRIPT"; then
            print_success "System dependencies installed successfully"
            echo ""
            # Reload environment
            if [ -f ~/.bashrc ]; then
                source ~/.bashrc 2>/dev/null || true
            fi
            # After install_system_dependencies.sh runs, post_install_build.sh will be called automatically
            # So we can skip the separate post-install build check
            POST_INSTALL_BUILD_NEEDED=0
        else
            print_error "System dependencies installation failed!"
            echo ""
            print_warning "Please install dependencies manually and try again."
            exit 1
        fi
    else
        print_error "install_system_dependencies.sh not found: $DEPENDENCIES_SCRIPT"
        echo ""
        print_warning "Please install dependencies manually and try again."
        exit 1
    fi
else
    print_success "System dependencies are installed"
    echo ""
    
    # If system dependencies are installed but post-install build is needed
    if [ $POST_INSTALL_BUILD_NEEDED -eq 1 ]; then
        print_warning "Post-install build steps are missing:"
        if [ $FASTDDS_MANUAL_INSTALLED -eq 0 ]; then
            echo "  - Fast-DDS manual installation"
        fi
        if [ $MONITORING_BUILT -eq 0 ]; then
            echo "  - Monitoring application build"
        fi
        echo ""
        print_info "Running post-install build..."
        echo ""
        
        if [ -f "$POST_INSTALL_BUILD_SCRIPT" ]; then
            chmod +x "$POST_INSTALL_BUILD_SCRIPT"
            if bash "$POST_INSTALL_BUILD_SCRIPT"; then
                print_success "Post-install build completed successfully"
                echo ""
                # Reload environment after Fast-DDS installation
                if [ -f ~/.bashrc ]; then
                    source ~/.bashrc 2>/dev/null || true
                fi
                sudo ldconfig 2>/dev/null || true
            else
                print_warning "Post-install build failed (continuing anyway...)"
                echo ""
            fi
        else
            print_warning "post_install_build.sh not found: $POST_INSTALL_BUILD_SCRIPT"
            echo ""
        fi
    fi
fi

# Check if system is ready
print_info "Checking system status..."

SYSTEM_READY=1

# Check for built executables
if [ ! -d "$PROJECT_ROOT/IDL" ] || [ -z "$(find "$PROJECT_ROOT/IDL" -maxdepth 1 -name "*_idl_generated" -type d 2>/dev/null)" ]; then
    SYSTEM_READY=0
fi

# Check for monitoring executable
if [ ! -f "$PROJECT_ROOT/monitoring/build/monitor" ] || [ ! -x "$PROJECT_ROOT/monitoring/build/monitor" ]; then
    SYSTEM_READY=0
fi

# Check for certificates
CA_CERT="$PROJECT_ROOT/secure_dds/CA/mainca_cert.pem"
PC_NAME=$(hostname)
PC_CERT="$PROJECT_ROOT/secure_dds/participants/$PC_NAME/${PC_NAME}_cert.pem"

if [ ! -f "$CA_CERT" ] || [ ! -f "$PC_CERT" ]; then
    SYSTEM_READY=0
fi

# If system is not ready, run setup first
if [ $SYSTEM_READY -eq 0 ]; then
    print_warning "System is not ready. Running setup..."
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
    else
        print_error "Setup failed!"
        echo ""
        exit 1
    fi
else
    print_success "System is ready"
    echo ""
fi

# Now run the demo
print_info "Starting tests and demo..."
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

# Copy setup scripts
if [ -f "$PROJECT_ROOT/v1.0.0_alpha_setup.sh" ]; then
    cp "$PROJECT_ROOT/v1.0.0_alpha_setup.sh" AppDir/usr/share/dds-project/
    chmod +x AppDir/usr/share/dds-project/v1.0.0_alpha_setup.sh
fi

if [ -f "$PROJECT_ROOT/v1.0.0_alpha_run.sh" ]; then
    cp "$PROJECT_ROOT/v1.0.0_alpha_run.sh" AppDir/usr/share/dds-project/
    chmod +x AppDir/usr/share/dds-project/v1.0.0_alpha_run.sh
fi

# Create secure_dds directory structure (will be populated at runtime)
mkdir -p AppDir/usr/share/dds-project/secure_dds/CA/private
mkdir -p AppDir/usr/share/dds-project/secure_dds/participants

print_success "Project files copied"

# Build AppImage
print_info "[6/6] Building AppImage..."
APPIMAGE_NAME="DDS-Project-v1.0.0_alpha-x86_64.AppImage"

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

