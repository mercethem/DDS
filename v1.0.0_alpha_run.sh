#!/bin/bash
# DDS Project - Run Tests and Demo Script v1.0.0_alpha
# This script runs tests and starts the demo dashboard:
# 1. Runs test_idl_modules.sh to start test publishers/subscribers
# 2. Launches the demo dashboard

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
    echo "  DDS Project - Run Tests and Demo"
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

# Print banner
print_banner

echo "This script will:"
echo "  1. Start test publishers/subscribers for all IDL modules"
echo "  2. Launch the demo dashboard"
echo ""
echo "Press Ctrl+C to stop the demo when finished."
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# ========================================
# Run Tests and Demo
# ========================================
print_step "Running Tests and Demo"

TESTS_DEMO_SCRIPT="$PROJECT_ROOT/init/sh/run_tests_and_demo.sh"

if [ ! -f "$TESTS_DEMO_SCRIPT" ]; then
    print_error "run_tests_and_demo.sh not found: $TESTS_DEMO_SCRIPT"
    exit 1
fi

# Make script executable
chmod +x "$TESTS_DEMO_SCRIPT"

print_info "Starting test publishers/subscribers and demo dashboard..."
print_info "This will start test publishers/subscribers and launch the demo dashboard."
print_info "Press Ctrl+C to stop the demo when finished."
echo ""

# Run tests and demo
if bash "$TESTS_DEMO_SCRIPT"; then
    print_success "Tests and demo completed"
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 130 ]; then
        # Ctrl+C was pressed (SIGINT = 130)
        print_warning "Demo stopped by user (Ctrl+C)"
    else
        print_warning "Tests and demo exited with code: $EXIT_CODE"
    fi
fi

echo ""
print_step "Demo Session Ended"

echo ""
echo "To run again:"
echo "  bash v1.0.0_alpha_run.sh"
echo ""
echo "Or run components separately:"
echo "  bash init/sh/run_tests_and_demo.sh"
echo "  cd demo/run_demo && bash run_demo.sh"
echo ""

exit 0

