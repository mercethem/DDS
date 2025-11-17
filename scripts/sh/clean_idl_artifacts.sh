#!/bin/bash
# Clean Windows-specific build artifacts from IDL directories
# This prepares the project for Linux builds

echo "========================================"
echo "IDL Windows Artifacts Cleaner"
echo "========================================"
echo

# Get script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

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
echo "2. Run: ./scripts/sh/dynamic_ALL.sh"
echo "3. This will regenerate all IDL files for Linux"
echo
read -p "Press Enter to continue..."