# clean_idl_artifacts.sh

## Overview

`clean_idl_artifacts.sh` removes Windows-specific build artifacts from IDL directories. It prepares the project for Linux builds by cleaning Windows files.

## Purpose

- Removes Windows build artifacts (.exe, .vcxproj, .sln files)
- Cleans CMake cache files
- Removes Windows build directories
- Prepares project for cross-platform use

## How It Works

1. **Directory Discovery**: Finds all `*_idl_generated` directories
2. **File Removal**: Deletes Windows-specific files
3. **Directory Cleanup**: Removes Windows build directories
4. **CMake Cleanup**: Removes CMake cache files

## Usage

### Basic Usage

```bash
cd scripts/sh
bash clean_idl_artifacts.sh
```

### From Project Root

```bash
bash scripts/sh/clean_idl_artifacts.sh
```

## Files Removed

- `*.exe` - Windows executables
- `*.vcxproj*` - Visual Studio project files
- `*.sln` - Visual Studio solution files
- `CMakeCache.txt` - CMake cache
- `CMakeFiles/` - CMake generated files
- `x64/`, `Release/`, `Debug/` - Windows build directories

## Use Cases

- Before copying project to Linux
- After Windows build, before Linux build
- Cleaning up cross-platform artifacts
- Preparing for fresh Linux build

## Requirements

- Bash shell
- Write permissions to IDL directories

## Notes

- Only removes Windows-specific files
- Preserves Linux build artifacts
- Safe to run on Linux systems (no effect)
- Useful for project portability

