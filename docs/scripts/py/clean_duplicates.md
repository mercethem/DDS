# clean_duplicate_code.py

## Overview

`clean_duplicate_code.py` removes duplicate dynamic code blocks from generated C++ PublisherApp and SubscriberApp files. Specifically, it cleans duplicate `resolve_dds_root` lambda functions that may be accidentally inserted multiple times.

## Purpose

- Removes duplicate `resolve_dds_root` lambda function definitions
- Keeps only the first occurrence of the block
- Prevents compilation errors from duplicate definitions
- Maintains code cleanliness in generated files

## How It Works

1. **File Discovery**: Scans all `*PublisherApp.cxx` and `*SubscriberApp.cxx` files in `IDL/*_idl_generated/` directories
2. **Pattern Detection**: Searches for the pattern `auto resolve_dds_root = []() -> std::filesystem::path {`
3. **Duplicate Removal**: If multiple occurrences are found, keeps only the first block and removes others
4. **Block Identification**: Uses brace matching to identify complete lambda function blocks

## Usage

### Basic Usage

```bash
cd scripts/py
python3 clean_duplicate_code.py
```

### From Project Root

```bash
python3 scripts/py/clean_duplicate_code.py
```

### Via Setup Script

Automatically called by `init/sh/project_setup.sh` during the cleanup phase.

## What It Cleans

Removes duplicate blocks like:
```cpp
auto resolve_dds_root = []() -> std::filesystem::path {
    // ... lambda body ...
};
const std::filesystem::path dds_root = resolve_dds_root();
```

## Output

- Prints the number of duplicate blocks found for each file
- Shows which files were cleaned
- Returns success/failure status

## Requirements

- Python 3.x
- Read/write access to `IDL/*_idl_generated/` directories

## Integration

This script is called by:
- `init/sh/project_setup.sh` - During cleanup phase (STEP 2a)

## Notes

- Only processes files with more than one occurrence of the pattern
- Preserves the first occurrence and removes subsequent duplicates
- Safe to run multiple times (idempotent)

