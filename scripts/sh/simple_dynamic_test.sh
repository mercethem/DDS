#!/bin/bash
# Simple Dynamic Test Script - Linux Version
# Test all IDL modules dynamically by discovering *_idl_generated dirs

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "Simple Dynamic Test Script"
echo "========================================"
echo

# Get script directory and navigate to IDL directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
IDL_DIR="$PROJECT_ROOT/IDL"

echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo "IDL directory: $IDL_DIR"

cd "$IDL_DIR"

echo "[INFO] Scanning for *_idl_generated directories..."

# Initialize test variables
TEST_COUNT=0
SUCCESS_COUNT=0

# Function to start a process in new terminal
start_process() {
    local title="$1"
    local work_dir="$2"
    local executable="$3"
    local mode="$4"

    # Find available terminal emulator
    if command -v gnome-terminal >/dev/null 2>&1; then
        gnome-terminal --title="$title" -- bash -c "cd '$work_dir'; echo 'Starting $title...'; echo 'Executable: $executable $mode'; echo '----------------------------------------'; './$executable' $mode; echo; echo '----------------------------------------'; echo 'Process finished. Press Enter to close...'; read" &
    elif command -v xterm >/dev/null 2>&1; then
        xterm -title "$title" -e bash -c "cd '$work_dir'; echo 'Starting $title...'; echo 'Executable: $executable $mode'; echo '----------------------------------------'; './$executable' $mode; echo; echo '----------------------------------------'; echo 'Process finished. Press Enter to close...'; read" &
    elif command -v konsole >/dev/null 2>&1; then
        konsole --title "$title" -e bash -c "cd '$work_dir'; echo 'Starting $title...'; echo 'Executable: $executable $mode'; echo '----------------------------------------'; './$executable' $mode; echo; echo '----------------------------------------'; echo 'Process finished. Press Enter to close...'; read" &
    elif command -v alacritty >/dev/null 2>&1; then
        alacritty --title "$title" -e bash -c "cd '$work_dir'; echo 'Starting $title...'; echo 'Executable: $executable $mode'; echo '----------------------------------------'; './$executable' $mode; echo; echo '----------------------------------------'; echo 'Process finished. Press Enter to close...'; read" &
    elif command -v kitty >/dev/null 2>&1; then
        kitty --title "$title" bash -c "cd '$work_dir'; echo 'Starting $title...'; echo 'Executable: $executable $mode'; echo '----------------------------------------'; './$executable' $mode; echo; echo '----------------------------------------'; echo 'Process finished. Press Enter to close...'; read" &
    else
        echo -e "${RED}[ERROR] No terminal emulator found!${NC}"
        return 1
    fi

    return 0
}

# Discover and run all *_idl_generated modules
mapfile -t GEN_DIRS < <(find . -maxdepth 1 -type d -name "*_idl_generated" | sort)

for dir in "${GEN_DIRS[@]}"; do
    module_name="$(basename "$dir" | sed 's/_idl_generated$//')"
    ((TEST_COUNT++))
    echo "[$TEST_COUNT] Testing $module_name..."

    # Determine working directory (prefer build/ if exists)
    work_dir="$IDL_DIR/${module_name}_idl_generated"
    if [[ -d "$work_dir/build" ]]; then
        work_dir="$work_dir/build"
    fi

    # Find an executable containing 'main' in its name
    found_exe=""
    while IFS= read -r -d '' exe; do
        if [[ -x "$exe" && -f "$exe" ]]; then
            found_exe="$(basename "$exe")"
            break
        fi
    done < <(find "$work_dir" -maxdepth 1 -type f -name "*main*" -print0)

    if [[ -z "$found_exe" ]]; then
        echo -e "  ${YELLOW}No '*main*' executable found in: $work_dir${NC}"
        continue
    fi

    echo "  - Starting Publisher..."
    start_process "$module_name Publisher" "$work_dir" "$found_exe" "publisher"
    sleep 2
    echo "  - Starting Subscriber..."
    start_process "$module_name Subscriber" "$work_dir" "$found_exe" "subscriber"
    echo "  [OK] $module_name test started"
    ((SUCCESS_COUNT++))
    echo

done

echo "========================================"
echo "Simple Dynamic Test Summary:"
echo "========================================"
echo "Total modules: $TEST_COUNT"
echo "Successful: $SUCCESS_COUNT"
echo

if [[ $SUCCESS_COUNT -gt 0 ]]; then
    echo -e "${GREEN}[OK] Test completed successfully!${NC}"
else
    echo -e "${RED}[ERROR] No tests were successful!${NC}"
    echo
    echo "Check:"
    echo "  - Are there *_idl_generated folders?"
    echo "  - Are there 'build' folders with executables?"
    echo "  - Did the build process complete successfully?"
fi

echo "========================================"
echo
echo "Press Enter to continue..."
read