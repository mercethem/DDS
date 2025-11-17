# IDL_BUILDER.sh

## Overview

`IDL_BUILDER.sh` builds all IDL modules that have been generated. It finds all `*_idl_generated` directories and builds them using CMake.

## Purpose

- Builds all generated IDL modules
- Uses CMake for configuration and building
- Cleans CMake cache for portability
- Reports build results

## How It Works

1. **Module Discovery**: Finds all `*_idl_generated` directories
2. **CMake Configuration**: Runs `cmake ..` in each build directory
3. **Cache Cleanup**: Removes old CMake cache (for portability)
4. **Building**: Runs `make` or `ninja` to build
5. **Result Reporting**: Lists generated executables

## Usage

### Basic Usage

```bash
cd scripts/sh
bash IDL_BUILDER.sh
```

### From Project Root

```bash
bash scripts/sh/IDL_BUILDER.sh
```

### Via Alias

After environment setup:
```bash
dds-build
```

## Build Process

For each `*_idl_generated` directory:
1. Checks for `CMakeLists.txt`
2. Creates `build/` directory if needed
3. Cleans old CMake cache (removes `CMakeCache.txt` and `CMakeFiles/`)
4. Runs `cmake ..` for configuration
5. Runs `make` or `ninja` to build
6. Lists generated executables

## Build Output

Executables are created in:
- `IDL/<Module>_idl_generated/build/<Module>main`

## Requirements

- CMake installed
- Build system (make or ninja)
- C++ compiler (g++ or clang++)
- Fast-DDS libraries installed
- IDL modules must be generated first

## Integration

This script is called by:
- `setup.sh` - During build phase
- `dynamic_ALL.sh` - As final step
- Can be run standalone after IDL generation

## Notes

- Cleans CMake cache for portability (removes old PC paths)
- Supports both `make` and `ninja` build systems
- Shows which executables were created
- Stops on first build failure

