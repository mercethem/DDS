# set_period.sh

## Overview

`set_period.sh` is a wrapper script that runs the `set_period.py` Python script. It provides a convenient interface for setting publisher period values, handling both interactive and batch modes.

## Purpose

- Convenient wrapper for `set_period.py`
- Sets correct working directory (project root)
- Validates command-line arguments
- Provides user-friendly error messages
- Supports both interactive and batch execution modes

## How It Works

1. **Directory Navigation**: Changes to project root directory (two levels up from script location)
2. **Argument Validation**: Checks if period argument is provided and validates it
3. **Mode Selection**: 
   - No argument → Interactive mode
   - With argument → Batch mode (applies same value to all)
4. **Script Execution**: Runs `python3 scripts/py/set_period.py` with appropriate arguments
5. **Status Display**: Shows completion message and waits for user input

## Usage

### Interactive Mode

Set different period values for each publisher:

```bash
cd scripts/sh
bash set_period.sh
```

Or from project root:

```bash
bash scripts/sh/set_period.sh
```

### Batch Mode

Apply the same period value to all publishers:

```bash
bash scripts/sh/set_period.sh 200
```

## Command-Line Arguments

### No Arguments (Interactive Mode)

```bash
./set_period.sh
```

- Starts interactive mode
- Prompts for each publisher file individually
- Allows different values for each file

### With Period Argument (Batch Mode)

```bash
./set_period.sh <period_in_ms>
```

- Applies the same period value to all publishers
- Period must be a positive integer (> 0)
- Example: `./set_period.sh 200` sets all to 200ms

## Argument Validation

The script validates the period argument:
- Must be a positive integer
- Must start with 1-9 (not zero)
- Invalid input shows error message and usage instructions

**Valid examples:**
- `200` ✓
- `1000` ✓
- `50` ✓

**Invalid examples:**
- `0` ✗ (must be positive)
- `-100` ✗ (must be positive)
- `abc` ✗ (must be integer)

## What It Does

### Interactive Mode

1. Displays "Starting interactive mode..." message
2. Executes `python3 scripts/py/set_period.py`
3. User interacts with Python script to set individual values
4. Shows completion status

### Batch Mode

1. Validates period argument
2. Displays "Running: set_period.py (period=X ms)..." message
3. Executes `python3 scripts/py/set_period.py X`
4. All files updated with same value
5. Shows completion status

## Directory Structure

The script assumes this structure:
```
project_root/
├── scripts/
│   ├── py/
│   │   └── set_period.py
│   └── sh/
│       └── set_period.sh
├── IDL/
│   └── *_idl_generated/
│       └── *PublisherApp.hpp
└── scenarios/
```

## Execution Flow

```
User runs script
    ↓
Navigate to project root
    ↓
Check arguments
    ↓
┌─────────────────┬─────────────────┐
│ No arguments    │ With argument    │
│ (Interactive)   │ (Batch)          │
└─────────────────┴─────────────────┘
    ↓                    ↓
Run Python script    Validate argument
    ↓                    ↓
User interaction    Run Python script
    ↓                    ↓
Show status         Show status
    ↓                    ↓
Wait for Enter      Wait for Enter
```

## Error Handling

- **Invalid period**: Shows error message with usage instructions
- **Python script errors**: Exit code is preserved and displayed
- **Missing Python**: System error (Python 3 required)
- **Wrong directory**: Script navigates to correct location automatically

## Exit Codes

- `0` - Success (operation completed successfully)
- `1` - Error (validation failed or Python script error)

## User Interaction

After execution:
- Shows success or error message
- Prompts: "Press Enter to continue..."
- Waits for user input before closing terminal (if run in GUI)

## Requirements

- Bash shell
- Python 3.x installed
- `set_period.py` must exist at `scripts/py/set_period.py`
- Project structure with `IDL/` directory

## Integration

Can be used:
- Standalone to configure publisher periods
- As part of setup scripts
- In automated workflows (with period argument)
- For manual configuration (interactive mode)

## Advantages Over Direct Python Execution

1. **Automatic directory navigation**: Always runs from project root
2. **Argument validation**: Catches errors before Python execution
3. **User-friendly messages**: Clear error messages and instructions
4. **Consistent interface**: Same interface as other shell scripts
5. **Terminal handling**: Waits for user input before closing

## Example Usage Scenarios

### Scenario 1: Quick Batch Update

```bash
# Set all publishers to 200ms
./set_period.sh 200
```

### Scenario 2: Individual Configuration

```bash
# Interactive mode - set different values
./set_period.sh
# Then follow prompts for each file
```

### Scenario 3: From Any Directory

```bash
# Works from any location
cd /some/other/directory
/path/to/project/scripts/sh/set_period.sh 150
```

## Notes

- Script automatically navigates to project root
- Works from any directory
- Period values are in milliseconds
- Changes are applied immediately
- No backup files are created (consider version control)
- Interactive mode allows early exit with 'exit' or 'q'

## Related Scripts

- `set_period.py` - The Python script that does the actual work
- Other shell scripts follow similar patterns

