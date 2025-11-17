# idl_patcher.sh

## Overview

`idl_patcher.sh` is a wrapper script that runs the IDL patcher Python script. It navigates to the project root and executes `idl_patcher.py`.

## Purpose

- Convenient wrapper for `idl_patcher.py`
- Sets correct working directory
- Provides simple execution interface
- Shows project root information

## How It Works

1. **Directory Navigation**: Changes to project root
2. **Script Execution**: Runs `python3 scripts/py/idl_patcher.py`
3. **Status Display**: Shows completion message

## Usage

### Basic Usage

```bash
cd scripts/sh
bash idl_patcher.sh
```

### From Project Root

```bash
bash scripts/sh/idl_patcher.sh
```

## What It Does

Executes the IDL patcher which:
- Parses IDL files
- Generates default data assignments
- Patches PublisherApp files

## Requirements

- Python 3.x
- `idl_patcher.py` must exist
- IDL files must be generated first

## Integration

Can be used:
- Standalone after IDL generation
- As part of manual workflow
- Alternative to running Python script directly

## Notes

- Simple wrapper script
- Sets project root automatically
- Waits for user input before closing
- Provides convenient execution method

