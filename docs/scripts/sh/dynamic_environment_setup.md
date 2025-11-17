# dynamic_environment_setup.sh

## Overview

`dynamic_environment_setup.sh` detects and configures the DDS project environment. It finds Python, Java, and CMake installations and creates environment configuration files.

## Purpose

- Detects Python, Java, and CMake installations
- Creates `dds_environment_linux.sh` with detected paths
- Creates `dds_aliases_linux.sh` with convenience aliases
- Verifies tool availability

## How It Works

1. **Tool Detection**: Runs `dynamic_finder.sh` to detect tools
2. **Path Detection**: Dynamically finds project root
3. **Environment File Creation**: Generates `dds_environment_linux.sh`
4. **Aliases Creation**: Generates `dds_aliases_linux.sh`
5. **Verification**: Checks that all tools are available

## Usage

### Basic Usage

```bash
cd scripts/sh
bash dynamic_environment_setup.sh
```

### From Project Root

```bash
bash scripts/sh/dynamic_environment_setup.sh
```

### Via Alias

After setup, use:
```bash
dds-env
```

## Generated Files

### dds_environment_linux.sh
Contains:
- Project paths (DDS_PROJECT_ROOT, DDS_IDL_DIR, etc.)
- Tool paths (Python, Java, CMake)
- Environment variables
- Library paths

### dds_aliases_linux.sh
Contains convenience aliases:
- `dds-build` - Build all modules
- `dds-clean` - Clean generated files
- `dds-security` - Apply security patches
- `dds-patch-idl` - Run IDL patcher
- `dds-patch-json` - Run JSON patcher
- `dds-demo` - Start demo server
- Navigation aliases (`cd-dds`, `cd-idl`, `cd-scripts`)

## Tool Detection

Detects tools in this order:
1. System PATH (`which` command)
2. Common installation paths
3. Anaconda/Miniconda installations
4. System default locations

## Verification

After setup, verifies:
- ✅ Python availability and version
- ✅ Java availability and version
- ✅ CMake availability and version
- ✅ Fast-DDS generator (fastddsgen)
- ✅ Build system (make/ninja)
- ✅ C++ compiler (g++/clang++)

## Requirements

- Bash shell
- At least Python 3.x installed
- Java (for fastddsgen)
- CMake

## Integration

This script is called by:
- `setup.sh` - During environment setup
- `dynamic_ALL.sh` - As STEP 1
- Can be run standalone to refresh environment

## Notes

- Regenerates environment files each time
- Uses dynamic path detection (portable)
- Provides detailed tool information
- Creates both environment and alias files

