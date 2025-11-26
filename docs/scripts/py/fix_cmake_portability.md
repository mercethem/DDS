# fix_cmake_rpath.py

## Overview

`fix_cmake_rpath.py` makes CMakeLists.txt files portable by removing hardcoded paths and adding RPATH settings. This ensures that binaries work correctly when the project is moved to different locations.

## Purpose

- Removes hardcoded OpenSSL paths
- Uses `find_package(OpenSSL)` instead of hardcoded paths
- Adds RPATH settings for portable binaries
- Ensures cross-platform compatibility

## How It Works

1. **File Discovery**: Finds all `CMakeLists.txt` files in `IDL/*_idl_generated/` directories
2. **OpenSSL Fix**: Replaces hardcoded OpenSSL paths with `find_package(OpenSSL REQUIRED)`
3. **RPATH Addition**: Adds RPATH settings for relative library paths
4. **Executable Properties**: Sets RPATH properties on executables

## Usage

### Basic Usage

```bash
cd scripts/py
python3 fix_cmake_rpath.py
```

### From Project Root

```bash
python3 scripts/py/fix_cmake_rpath.py
```

### Via Setup Script

Automatically called by `init/sh/project_setup.sh` during CMake portability fix phase.

## Changes Made

### 1. OpenSSL Configuration

**Before:**
```cmake
set(OPENSSL_ROOT_DIR "/usr")
set(OPENSSL_LIBRARIES "/usr/lib/x86_64-linux-gnu/libssl.so")
include_directories(/usr/include/openssl)
```

**After:**
```cmake
find_package(OpenSSL REQUIRED)
target_link_libraries(${EXEC_NAME} OpenSSL::SSL OpenSSL::Crypto)
```

### 2. RPATH Settings

Adds:
```cmake
set(CMAKE_BUILD_RPATH_USE_ORIGIN TRUE)
set(CMAKE_BUILD_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib:/usr/local/lib")
```

### 3. Executable Properties

Adds:
```cmake
set_target_properties(${EXEC_NAME} PROPERTIES
    BUILD_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib"
    INSTALL_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib"
)
```

## Output

- Prints which files were modified
- Shows what changes were made
- Returns count of updated files

## Requirements

- Python 3.x
- Read/write access to `IDL/*_idl_generated/CMakeLists.txt` files

## Integration

This script is called by:
- `init/sh/project_setup.sh` - During CMake portability fix phase (STEP 2b)

## Notes

- Only modifies files that need changes
- Preserves existing CMake structure
- Safe to run multiple times (idempotent)
- Uses `$ORIGIN` for relative RPATH (portable)

