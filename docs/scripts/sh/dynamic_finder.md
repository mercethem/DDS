# dynamic_finder.sh

## Overview

`dynamic_finder.sh` detects Python, Java, and CMake installations on the system. It searches common installation paths and creates an environment file with detected tool paths.

## Purpose

- Finds Python 3.x installations
- Finds Java installations
- Finds CMake installations
- Creates `dds_environment.sh` with detected paths

## How It Works

1. **Python Detection**: Searches system PATH and common locations
2. **Java Detection**: Searches system PATH and common locations
3. **CMake Detection**: Searches system PATH and common locations
4. **File Creation**: Writes detected paths to `dds_environment.sh`

## Usage

### Basic Usage

```bash
cd scripts/sh
bash dynamic_finder.sh
```

### Usually Called By

- `dynamic_environment_setup.sh` - As part of environment setup

## Detection Order

### Python
1. System `python3` command
2. System `python` command (if Python 3)
3. Common paths: `/usr/bin/python3`, `/usr/local/bin/python3`
4. Version-specific: `python3.12`, `python3.11`, etc.
5. Anaconda/Miniconda installations

### Java
1. System `java` command
2. Common paths: `/usr/bin/java`, `/usr/local/bin/java`
3. JAVA_HOME environment variable
4. Version-specific: `java-11`, `java-17`, etc.

### CMake
1. System `cmake` command
2. Common paths: `/usr/bin/cmake`, `/usr/local/bin/cmake`
3. Version-specific: `cmake3`

## Output File

Creates `scripts/sh/dds_environment.sh` with:
```bash
export DDS_PYTHON_PATH="/detected/path/to/python3"
export DDS_JAVA_PATH="/detected/path/to/java"
export DDS_CMAKE_PATH="/detected/path/to/cmake"
```

## Requirements

- Bash shell
- At least one tool must be found (Python recommended)

## Integration

This script is called by:
- `dynamic_environment_setup.sh` - Tool detection phase

## Notes

- Provides colored output for better visibility
- Shows which tool was found at which path
- Creates environment file for other scripts to use
- Handles multiple installation scenarios

