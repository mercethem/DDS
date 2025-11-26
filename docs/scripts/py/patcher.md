# idl_json_patcher.py

## Overview

`idl_json_patcher.py` is a legacy IDL patcher that adds JSON file reading functionality to C++ Publisher applications. It analyzes IDL files and patches PublisherApp files to read data from JSON files.

## Purpose

- Adds JSON file reading capability to Publisher applications
- Parses IDL files to understand data structures
- Generates code for reading JSON data
- Supports multiple IDL modules

## How It Works

1. **IDL Analysis**: Parses IDL files to extract data structures
2. **JSON Matching**: Matches publishers with JSON scenario files
3. **Code Generation**: Generates JSON reading code
4. **File Patching**: Patches PublisherApp files with generated code

## Usage

### Basic Usage

```bash
cd scripts/py
python3 idl_json_patcher.py
```

### From Project Root

```bash
python3 scripts/py/idl_json_patcher.py
```

## Note

This script is a legacy version. For new projects, use:
- `idl_default_data_patcher.py` - For default data generation
- `json_reading_patcher.py` - For JSON file reading

## Requirements

- Python 3.x
- IDL files in `IDL/` directory
- JSON scenario files in `scenarios/` directory

## Notes

- Legacy script, may be deprecated
- Consider using `idl_default_data_patcher.py` + `json_reading_patcher.py` instead

