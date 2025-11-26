# generate_idl_code.sh

## Overview

`generate_idl_code.sh` generates C++ code from IDL files using Fast-DDS generator (fastddsgen). It processes all `.idl` files in the `IDL/` directory and creates `*_idl_generated` directories with C++ code.

## Purpose

- Generates C++ code from IDL files
- Creates PublisherApp, SubscriberApp, and type definitions
- Downloads JSON library if missing
- Configures OpenSSL paths dynamically

## How It Works

1. **Portability Check**: Verifies project structure
2. **Java Check**: Verifies Java is installed (required for fastddsgen)
3. **JSON Library**: Downloads nlohmann/json if missing
4. **OpenSSL Detection**: Finds OpenSSL paths dynamically
5. **IDL Processing**: Runs fastddsgen on each `.idl` file
6. **Output**: Creates `*_idl_generated` directories

## Usage

### Basic Usage

```bash
cd scripts/sh
bash generate_idl_code.sh
```

### From Project Root

```bash
bash scripts/sh/generate_idl_code.sh
```

### Via Alias

After environment setup:
```bash
dds-build
```

## Generated Structure

For each IDL file (e.g., `CoreData.idl`). See `generate_idl_code.mdd` for the complete generated structure diagram.

## Requirements

- Java (for fastddsgen)
- Fast-DDS generator (fastddsgen) installed
- OpenSSL development libraries
- Internet connection (for JSON library download)

## JSON Library

Automatically downloads nlohmann/json v3.11.3 to:
- `include/nlohmann/json.hpp`

## OpenSSL Configuration

Dynamically finds OpenSSL:
- Searches common installation paths
- Configures include and library paths
- Uses `find_package(OpenSSL)` in CMakeLists.txt

## Integration

This script is called by:
- `init/sh/project_setup.sh` - During IDL generation phase
- `run_complete_workflow.sh` - As STEP 2
- `build_idl_modules.sh` - Before building

## Notes

- Must be run from `scripts/sh` directory
- Checks for required folders before execution
- Downloads JSON library automatically if missing
- Portable: uses dynamic path detection

