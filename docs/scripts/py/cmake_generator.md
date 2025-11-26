# generate_cmake_files.py

## Overview

`generate_cmake_files.py` generates cross-platform CMakeLists.txt files for IDL modules. It creates standardized CMake configuration files that work on both Windows and Linux systems.

## Purpose

- Generates CMakeLists.txt files for `*_idl_generated` directories
- Ensures cross-platform compatibility
- Uses templates for consistent structure
- Supports multiple IDL modules

## How It Works

1. **Module Discovery**: Finds all `*_idl_generated` directories
2. **Template Loading**: Loads CMakeLists template (if available)
3. **File Generation**: Creates CMakeLists.txt for each module
4. **Configuration**: Sets module-specific variables

## Usage

### Basic Usage

```bash
cd scripts/py
python3 generate_cmake_files.py
```

### From Project Root

```bash
python3 scripts/py/generate_cmake_files.py
```

## Template Location

Looks for template at:
- `cross-platform/templates/CMakeLists_template.txt`

If template doesn't exist, generates standard CMakeLists.txt.

## Generated CMakeLists.txt Structure

- Fast-DDS dependency
- OpenSSL dependency
- Module-specific settings
- Executable targets
- Library targets

## Requirements

- Python 3.x
- IDL modules must be generated first (via `generate_idl_code.sh`)

## Notes

- Usually not needed if CMakeLists.txt already exist
- Useful for creating new modules or regenerating files
- Cross-platform compatible output

