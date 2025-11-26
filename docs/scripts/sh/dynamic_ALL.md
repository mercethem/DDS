# run_complete_workflow.sh

## Overview

`run_complete_workflow.sh` is the main orchestrator script that runs the complete DDS workflow. It executes all necessary steps in the correct order: environment setup, IDL generation, domain ID updates, security setup, patching, and building.

## Purpose

- Orchestrates the complete DDS project setup workflow
- Runs all steps in the correct sequence
- Provides error handling and status reporting
- Ensures portability with dynamic path detection

## How It Works

The script executes the following steps in order:

1. **Environment Setup** - Configures environment variables and detects tools
2. **IDL Generation** - Generates C++ code from IDL files
3. **Domain ID Update** - Updates domain IDs in generated code
4. **Security Setup** - Creates certificates and applies security settings
5. **Patching** - Applies IDL and JSON patches
6. **Building** - Builds all IDL modules

## Usage

### Basic Usage

```bash
cd scripts/sh
bash run_complete_workflow.sh
```

### From Project Root

```bash
bash scripts/sh/run_complete_workflow.sh
```

### Via Setup Script

Automatically called by `init/sh/project_setup.sh` as the main workflow.

## Execution Steps

### STEP 1: Environment Setup
- Runs `setup_environment.sh`
- Detects Python, Java, CMake
- Creates environment configuration files

### STEP 2: IDL Generation
- Runs `generate_idl_code.sh`
- Generates C++ code from `.idl` files
- Creates `*_idl_generated` directories

### STEP 3: Domain ID Update
- Runs `update_domain_ids.sh`
- Updates domain IDs in `*main.cxx` files
- Reads domain IDs from IDL file comments

### STEP 4: Security Setup
- Runs `setup_security_certificates.sh`
- Creates certificates if needed
- Applies security patches

### STEP 5: IDL Patcher Setup
- Runs `idl_default_data_patcher.py`
- Patches PublisherApp files with default data

### STEP 6: JSON Patcher Setup
- Runs `json_reading_patcher.py`
- Replaces hardcoded data with JSON reading

### STEP 7: Building
- Runs `build_idl_modules.sh`
- Builds all IDL modules
- Creates executables

## Error Handling

- Stops on first error
- Provides clear error messages
- Shows which step failed

## Requirements

- Bash shell
- All required tools (Python, Java, CMake, Fast-DDS)
- Execute permissions on script files

## Integration

This script is called by:
- `init/sh/project_setup.sh` - Main setup script

## Notes

- Must be run from `scripts/sh` directory
- Checks project structure before execution
- Provides progress feedback for each step
- Complete workflow automation

