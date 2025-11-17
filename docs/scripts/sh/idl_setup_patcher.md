# idl_setup_patcher.sh

## Overview

`idl_setup_patcher.sh` is a wrapper script that runs the IDL setup patcher Python script. It navigates to the project root and executes `idl_setup_patcher.py`.

## Purpose

- Convenient wrapper for `idl_setup_patcher.py`
- Sets correct working directory
- Provides simple execution interface
- Shows project root information

## How It Works

1. **Directory Navigation**: Changes to project root
2. **Script Execution**: Runs `python3 scripts/py/idl_setup_patcher.py`
3. **Status Display**: Shows completion message

## Usage

### Basic Usage

```bash
cd scripts/sh
bash idl_setup_patcher.sh
```

### From Project Root

```bash
bash scripts/sh/idl_setup_patcher.sh
```

## What It Does

Executes the IDL setup patcher which:
- Extracts data fields from header files
- Adds JSON printing code to Publisher/Subscriber files
- Enables data visualization

## Requirements

- Python 3.x
- `idl_setup_patcher.py` must exist
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

