#!/bin/bash
set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Always run from this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$DEMO_DIR"

echo -e "${CYAN}========================================"
echo "   DEMO BUILD_DEMO SCRIPT"
echo "   Node.js Dependencies Installer"
echo "========================================"
echo -e "${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js not found!${NC}"
    echo -e "${YELLOW}Please install Node.js to continue.${NC}"
    echo ""
    echo "Installation instructions:"
    echo "  Ubuntu/Debian: sudo apt install nodejs npm"
    echo "  Or download from: https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}[ERROR] npm not found!${NC}"
    echo -e "${YELLOW}Please install npm to continue.${NC}"
    echo ""
    echo "Installation instructions:"
    echo "  Ubuntu/Debian: sudo apt install npm"
    echo "  Or download from: https://nodejs.org/ (includes npm)"
    exit 1
fi

# Display versions
NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo -e "${GREEN}[OK] Node.js version: ${NODE_VERSION}${NC}"
echo -e "${GREEN}[OK] npm version: ${NPM_VERSION}${NC}"
echo ""

# Check if package.json exists
if [ ! -f "$DEMO_DIR/package.json" ]; then
    echo -e "${RED}[ERROR] package.json not found in ${DEMO_DIR}${NC}"
    exit 1
fi

echo -e "${BLUE}[STEP] Installing Node.js dependencies...${NC}"
echo ""

# Install dependencies
npm install

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Dependency installation failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}[OK] Dependencies installed successfully!${NC}"
echo ""

# Verify node_modules directory
if [ -d "$DEMO_DIR/node_modules" ]; then
    MODULE_COUNT=$(find "$DEMO_DIR/node_modules" -maxdepth 1 -type d | wc -l)
    echo -e "${GREEN}[OK] node_modules directory created with ${MODULE_COUNT} packages${NC}"
else
    echo -e "${YELLOW}[WARNING] node_modules directory not found after installation${NC}"
fi

echo ""
echo -e "${CYAN}========================================"
echo "   BUILD_DEMO COMPLETED"
echo "========================================"
echo -e "${NC}"
echo -e "${GREEN}Demo is ready to run!${NC}"
echo ""
echo "To start the demo:"
echo "  Linux:   ./run_demo/run_demo.sh"
echo "  Windows: run_demo\\run_demo.bat"
echo ""
echo "Or manually:"
echo "  npm start"
echo ""

exit 0

