#!/bin/bash
# Clean Windows-specific build artifacts from IDL directories
# This prepares the project for Linux builds

echo "========================================"
echo "IDL Windows Artifacts Cleaner"
echo "========================================"
echo

# Get script directory and project root dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

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

IDL_DIR="IDL"

if [ ! -d "$IDL_DIR" ]; then
    echo "[ERROR] IDL directory not found!"
    exit 1
fi

echo "[INFO] Cleaning Windows build artifacts from IDL directories..."
echo

# Find all *_idl_generated directories
for idl_gen_dir in "$IDL_DIR"/*_idl_generated; do
    if [ -d "$idl_gen_dir" ]; then
        echo "[CLEAN] Processing: $(basename "$idl_gen_dir")"
        
        # Remove Windows-specific files
        find "$idl_gen_dir" -name "*.vcxproj*" -delete 2>/dev/null
        find "$idl_gen_dir" -name "*.sln" -delete 2>/dev/null
        find "$idl_gen_dir" -name "*.exe" -delete 2>/dev/null
        find "$idl_gen_dir" -name "CMakeCache.txt" -delete 2>/dev/null
        
        # Remove Windows build directories
        rm -rf "$idl_gen_dir/x64" 2>/dev/null
        rm -rf "$idl_gen_dir/Release" 2>/dev/null
        rm -rf "$idl_gen_dir/Debug" 2>/dev/null
        rm -rf "$idl_gen_dir"/*.dir 2>/dev/null
        rm -rf "$idl_gen_dir/CMakeFiles" 2>/dev/null
        
        echo "  - Removed Windows artifacts"
    fi
done

echo
echo "[OK] Windows artifacts cleanup completed!"
echo
echo "Next steps for Linux:"
echo "1. Copy project to Linux system"
echo "2. Run: $PROJECT_ROOT/scripts/sh/run_complete_workflow.sh"
echo "3. This will regenerate all IDL files for Linux"
echo
