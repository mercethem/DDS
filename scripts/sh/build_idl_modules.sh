#!/bin/bash
# Fast DDS Project - Simplified Build Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
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

IDL_DIR="$PROJECT_ROOT/IDL"

printf "${BLUE}DDS Simple Build - Only builds in existing _idl_generated directories${NC}\n"

mapfile -t GEN_DIRS < <(find "$IDL_DIR" -maxdepth 1 -type d -name "*_idl_generated" | sort)
if [[ ${#GEN_DIRS[@]} -eq 0 ]]; then
    printf "${RED}No _idl_generated directories found!${NC}\n"
    exit 1
fi

for d in "${GEN_DIRS[@]}"; do
    mod=$(basename "$d" | sed 's/_idl_generated$//')
    echo "[INFO] Building: $mod ($d)"
    cd "$d"
    if [[ -f "CMakeLists.txt" ]]; then
        if [[ ! -d build ]]; then mkdir build; fi
        cd build
        # Clean CMake cache (for portability - old PC paths may remain in cache)
        if [[ -f CMakeCache.txt ]]; then
            echo "[INFO] Cleaning CMake cache (for portability)..."
            rm -f CMakeCache.txt
            rm -rf CMakeFiles/
        fi
        cmake ..
        if command -v ninja >/dev/null 2>&1 && [[ -f ../build.ninja ]]; then
            ninja
        else
            make
        fi
        echo -e "${GREEN}[OK] Build complete: $d/build${NC}"
        echo -e "${YELLOW}Found executables:${NC}"
        for exe in *; do
            if [[ -x "$exe" && -f "$exe" && ! -d "$exe" ]]; then
                echo "  - $d/build/$exe"
            fi
        done
        cd ..
    else
        echo -e "${YELLOW}CMakeLists.txt not found, skipping: $d${NC}"
        continue
    fi
    cd "$PROJECT_ROOT"
done

echo -e "\n${GREEN}All build operations completed. Outputs are in respective _idl_generated/build directories.${NC}\n"