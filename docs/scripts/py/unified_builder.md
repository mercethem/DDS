# unified_build_system.py

## Overview

`unified_build_system.py` provides a cross-platform build system for the DDS project. It automatically detects the platform (Windows/Linux) and uses appropriate build tools (CMake, Make/Ninja, MSBuild).

## Purpose

- Cross-platform build automation
- Dependency checking (CMake, compiler, Fast-DDS)
- Automatic platform detection
- Unified build interface for Windows and Linux

## How It Works

1. **Platform Detection**: Detects Windows or Linux automatically
2. **Dependency Check**: Verifies CMake, compiler, and build tools
3. **Project Discovery**: Finds all `*_idl_generated` directories
4. **Build Execution**: Runs CMake configuration and build for each module
5. **Error Handling**: Provides detailed error messages and status

## Usage

### Basic Usage

```bash
cd scripts/py
python3 unified_build_system.py
```

### From Project Root

```bash
python3 scripts/py/unified_build_system.py
```

## Platform Support

### Linux
- Uses `make` or `ninja` as build system
- Checks for `gcc`/`g++` compiler
- Supports parallel builds with `nproc`

### Windows
- Uses `MSBuild` or `ninja` as build system
- Checks for Visual Studio compiler
- Supports parallel builds

## Dependency Checks

The script verifies:
- ✅ CMake availability
- ✅ Build system (make/ninja/MSBuild)
- ✅ Fast-DDS generator (fastddsgen)
- ✅ C++ compiler (g++/cl)

## Build Process

For each `*_idl_generated` directory:
1. Creates `build/` directory if needed
2. Runs `cmake ..` for configuration
3. Runs build command (`make`, `ninja`, or `MSBuild`)
4. Reports success/failure

## Output

- Shows dependency status
- Displays build progress for each module
- Reports build results (success/failure)
- Lists generated executables

## Requirements

- Python 3.x
- CMake installed
- Build system (make/ninja/MSBuild)
- C++ compiler
- Fast-DDS libraries

## Integration

Can be used as an alternative to:
- `scripts/sh/build_idl_modules.sh` - Linux build script
- Manual CMake builds

## Notes

- Cross-platform: works on Windows and Linux
- Automatic tool detection
- Parallel builds for faster compilation
- Detailed error reporting

