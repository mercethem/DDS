#!/bin/bash

# Get script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Check if period argument is provided
if [ $# -eq 0 ]; then
    echo "Starting interactive mode..."
    echo "You can enter different values for each file."
    echo
    # Run in interactive mode (no arguments)
    python3 scripts/py/set_period.py
else
    PERIOD=$1
    
    # Validate that PERIOD is a positive integer
    if ! [[ "$PERIOD" =~ ^[1-9][0-9]*$ ]]; then
        echo "ERROR: Period must be a positive integer!"
        echo "Usage: ./set_period.sh [period_in_ms]"
        echo "Example: ./set_period.sh 200"
        echo "         (without argument: interactive mode)"
        exit 1
    fi
    
    echo "Running: set_period.py (period=$PERIOD ms)..."
    echo "Note: All files will be updated with the same value."
    echo "      Run without argument for interactive mode: ./set_period.sh"
    echo
    
    # Run with period argument (non-interactive mode)
    python3 scripts/py/set_period.py "$PERIOD"
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

