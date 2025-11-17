# idl_setup_patcher.py

## Overview

`idl_setup_patcher.py` patches PublisherApp and SubscriberApp files to add JSON data printing functionality. It extracts data fields from header files and adds code to print sample data in JSON format.

## Purpose

- Adds JSON printing code to Publisher/Subscriber applications
- Extracts data fields from header files automatically
- Enables data visualization and debugging
- Works with all IDL modules

## How It Works

1. **Module Discovery**: Finds all `*_idl_generated` directories
2. **Header Parsing**: Extracts member variables from header files
3. **Code Injection**: Adds JSON printing code to PublisherApp/SubscriberApp
4. **Field Mapping**: Maps C++ types to JSON format

## Usage

### Basic Usage

```bash
cd scripts/py
python3 idl_setup_patcher.py
```

### From Project Root

```bash
python3 scripts/py/idl_setup_patcher.py
```

### Via Shell Script

```bash
bash scripts/sh/idl_setup_patcher.sh
```

## What It Does

Adds code to print sample data in JSON format:
```cpp
std::cout << " - {" << std::endl;
std::cout << "  \"latitude\": " << sample_.latitude() << "," << std::endl;
std::cout << "  \"longitude\": " << sample_.longitude() << "," << std::endl;
// ... more fields ...
std::cout << "}" << std::endl;
```

## Output Format

Prints data in JSON format to stdout:
```json
 - {
  "latitude": 39.9334,
  "longitude": 32.8597,
  "altitude": 1500.0,
  "speed_mps": 250.5
}
```

## Requirements

- Python 3.x
- Generated `*_idl_generated` directories
- Header files with member variables

## Integration

This script is called by:
- `scripts/sh/idl_setup_patcher.sh` - Standalone execution
- Can be integrated into build/test workflows

## Notes

- Only adds printing code, doesn't modify existing functionality
- Extracts fields automatically from headers
- Handles nested structures
- Safe to run multiple times

