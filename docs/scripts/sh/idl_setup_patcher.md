# patch_idl_setup.sh

## Overview

`patch_idl_setup.sh` is a wrapper script that runs the IDL setup patcher Python script. It navigates to the project root and executes `idl_setup_data_printer.py`.

## Purpose

- Convenient wrapper for `idl_setup_data_printer.py`
- Sets correct working directory
- Provides simple execution interface
- Shows project root information

## How It Works

1. **Directory Navigation**: Changes to project root
2. **Script Execution**: Runs `python3 scripts/py/idl_setup_data_printer.py`
3. **Status Display**: Shows completion message

## Usage

### Basic Usage

```bash
cd scripts/sh
bash patch_idl_setup.sh
```

### From Project Root

```bash
bash scripts/sh/patch_idl_setup.sh
```

## What It Does

Executes the IDL setup patcher which:
- Extracts data fields from header files
- Adds JSON printing code to Publisher/Subscriber files
- Enables data visualization

## Requirements

- Python 3.x
- `idl_setup_data_printer.py` must exist
- IDL modules must be generated first

## Integration

Can be used:
- Standalone after IDL generation
- For adding debugging output
- As part of test workflow

## Notes

- Simple wrapper script
- Sets project root automatically
- Waits for user input before closing
- Adds JSON printing functionality

