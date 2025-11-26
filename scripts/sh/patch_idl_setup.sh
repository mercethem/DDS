#!/bin/bash

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

# Verify and display the new working directory (Project Root)
echo "Project root set to: $(pwd)"
echo

echo "Running: idl_setup_data_printer.py..."

# Run the Python script with absolute path from project root
python3 "$PROJECT_ROOT/scripts/py/idl_setup_data_printer.py"

echo
echo "Operation completed."

exit 0