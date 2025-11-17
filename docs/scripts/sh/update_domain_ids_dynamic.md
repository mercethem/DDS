# update_domain_ids_dynamic.md

## Overview

`update_domain_ids_dynamic.sh` updates domain IDs in generated C++ code based on domain IDs specified in IDL file comments. It reads the domain ID from the first line of each IDL file and updates the corresponding generated code.

## Purpose

- Reads domain IDs from IDL file comments
- Updates domain IDs in `*main.cxx` files
- Ensures domain IDs match IDL specifications
- Supports multiple IDL modules

## How It Works

1. **IDL File Scanning**: Scans all `.idl` files in `IDL/` directory
2. **Domain ID Extraction**: Reads domain ID from first line comment: `//domain=0`
3. **Code Update**: Updates `int domain_id = X;` in `*main.cxx` files
4. **Verification**: Reports which files were updated

## Usage

### Basic Usage

```bash
cd scripts/sh
bash update_domain_ids_dynamic.sh
```

### From Project Root

```bash
bash scripts/sh/update_domain_ids_dynamic.sh
```

## IDL File Format

IDL files should have domain ID in first line:
```idl
//domain=0
module CoreData {
    // ... IDL definitions ...
};
```

## Generated Code Update

Updates code in `*main.cxx` files:
```cpp
// Before
int domain_id = 0;

// After (if IDL says //domain=5)
int domain_id = 5;
```

## Requirements

- Bash shell
- IDL files with domain comments
- Generated `*_idl_generated` directories

## Integration

This script is called by:
- `setup.sh` - During domain ID update phase
- `dynamic_ALL.sh` - As STEP 3

## Notes

- Reads domain ID from IDL file comments
- Updates only if domain comment is found
- Uses `sed` for in-place file editing
- Safe to run multiple times

