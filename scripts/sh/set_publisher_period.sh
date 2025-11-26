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

# Check if period argument is provided
if [ $# -eq 0 ]; then
    echo "Starting interactive mode..."
    echo "You can enter different values for each file."
    echo
    # Run in interactive mode (no arguments)
    python3 "$PROJECT_ROOT/scripts/py/set_publisher_period.py"
else
    PERIOD=$1
    
    # Validate that PERIOD is a positive integer
    if ! [[ "$PERIOD" =~ ^[1-9][0-9]*$ ]]; then
        echo "ERROR: Period must be a positive integer!"
        echo "Usage: ./set_publisher_period.sh [period_in_ms]"
        echo "Example: ./set_publisher_period.sh 200"
        echo "         (without argument: interactive mode)"
        exit 1
    fi
    
    echo "Running: set_publisher_period.py (period=$PERIOD ms)..."
    echo "Note: All files will be updated with the same value."
    echo "      Run without argument for interactive mode: ./set_publisher_period.sh"
    echo
    
    # Run with period argument (non-interactive mode)
    python3 "$PROJECT_ROOT/scripts/py/set_publisher_period.py" "$PERIOD"
fi

EXIT_CODE=$?

echo
if [ $EXIT_CODE -eq 0 ]; then
    echo "Operation completed successfully."
else
    echo "An error occurred during operation."
fi

read -p "Press Enter to continue..."

exit $EXIT_CODE

