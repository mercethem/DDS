# set_period.py

## Overview

`set_period.py` is an interactive tool for modifying the `period_ms_` value in all DDS Publisher application header files (`*PublisherApp.hpp`). It allows you to set different period values for each publisher or apply the same value to all publishers.

## Purpose

- Modify the publishing period for DDS publishers
- Set different periods for different publisher modules
- Update `const uint32_t period_ms_` values in header files
- Support both interactive and batch modes
- Dynamically detect project structure

## How It Works

1. **Project Detection**: Automatically detects project root by searching for `IDL` and `scenarios` directories
2. **File Discovery**: Finds all `*PublisherApp.hpp` files in `IDL/*_idl_generated/` directories
3. **Period Reading**: Reads current `period_ms_` values from each file
4. **Interactive Mode**: Prompts user for new period value for each file
5. **Batch Mode**: Applies the same period value to all files
6. **File Update**: Uses regex to replace `const uint32_t period_ms_ = <old_value>;` with new value

## Usage

### Interactive Mode (Recommended)

Allows setting different period values for each publisher:

```bash
cd scripts/py
python3 set_period.py
```

Or from project root:

```bash
python3 scripts/py/set_period.py
```

Or via shell script:

```bash
bash scripts/sh/set_period.sh
```

### Batch Mode

Apply the same period value to all publishers:

```bash
python3 scripts/py/set_period.py 200
```

Or via shell script:

```bash
bash scripts/sh/set_period.sh 200
```

## Interactive Mode Workflow

1. Script displays all found PublisherApp.hpp files with current period values
2. For each file, prompts: `[N/Total] ModuleName (Current: X ms):`
3. User can:
   - Enter a new period value (positive integer)
   - Press ENTER to keep current value
   - Type `exit` or `q` to finish early and apply changes
4. After all files are processed, changes are applied
5. Summary shows how many files were updated

## Example Interactive Session

```
============================================================
INTERACTIVE PERIOD SETTER
============================================================

Found 6 PublisherApp.hpp file(s):

  1. CoreData2            - Current: 1000 ms
  2. CoreData3            - Current: 1000 ms
  3. CoreData4            - Current: 1000 ms
  4. CoreData              - Current: 1000 ms
  5. Intelligence          - Current: 1000 ms
  6. Messaging             - Current: 1000 ms

------------------------------------------------------------
Enter new period value for each file.
Press ENTER to keep current value (no change).
Type 'exit' or 'q' to finish and apply changes.
------------------------------------------------------------

[1/6] CoreData2            (Current: 1000 ms): 200
  -> New value: 200 ms
[2/6] CoreData3            (Current: 1000 ms): 500
  -> New value: 500 ms
[3/6] CoreData4            (Current: 1000 ms): 
  -> Keeping current value: 1000 ms
...
```

## What Gets Modified

The script modifies the `period_ms_` constant in header files:

**Before:**
```cpp
const uint32_t period_ms_ = 100; // in ms
```

**After (example):**
```cpp
const uint32_t period_ms_ = 200; // in ms
```

## File Pattern Matching

The script uses regex pattern to find and replace:
- **Pattern**: `const\s+uint32_t\s+period_ms_\s*=\s*(\d+)\s*;`
- **Replacement**: Updates only the numeric value while preserving formatting

## Project Structure Detection

The script automatically detects the project root by:
1. Starting from current working directory
2. Walking up the directory tree
3. Looking for directories containing both `IDL` and `scenarios` folders
4. Using the first matching directory as project root

This makes the script portable and works regardless of where the project is located.

## Supported Files

The script processes all files matching:
- Pattern: `IDL/*_idl_generated/*PublisherApp.hpp`
- Examples:
  - `IDL/CoreData_idl_generated/CoreDataPublisherApp.hpp`
  - `IDL/CoreData2_idl_generated/CoreData2PublisherApp.hpp`
  - `IDL/Intelligence_idl_generated/IntelligencePublisherApp.hpp`
  - `IDL/Messaging_idl_generated/MessagingPublisherApp.hpp`

## Error Handling

- **Missing IDL directory**: Script exits with error message
- **No PublisherApp.hpp files found**: Script reports error and exits
- **Invalid period value**: Prompts user to enter valid positive integer
- **File read/write errors**: Displays error message and continues with next file
- **Missing period_ms_**: Warns user but continues processing

## Output

After processing, the script displays:
- Number of files successfully updated
- Number of files skipped (unchanged)
- Detailed update log for each file

## Requirements

- Python 3.x
- Project structure with `IDL/` and `scenarios/` directories
- `*PublisherApp.hpp` files containing `period_ms_` constant

## Integration

Can be used:
- Standalone to adjust publisher periods
- As part of configuration workflow
- Before running DDS applications
- To synchronize period values across publishers

## Notes

- Period values are in milliseconds
- Values must be positive integers (> 0)
- Script preserves file formatting and comments
- Changes are applied immediately (no backup created)
- Script is portable and works from any directory

## Related Scripts

- `set_period.sh` - Shell wrapper for easier execution
- Other patcher scripts modify different aspects of publisher applications

