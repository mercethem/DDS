# qos_settings_patcher_gui.py

## Overview

`qos_settings_patcher_gui.py` provides a graphical user interface (GUI) for the QoS patcher. It allows users to visually select modules and configure QoS settings without using command-line arguments.

## Purpose

- User-friendly GUI for QoS configuration
- Module and variation (Publisher/Subscriber) selection
- Simple and advanced QoS configuration modes
- Visual feedback and status display

## How It Works

1. **Module Discovery**: Automatically finds all `*_idl_generated` modules
2. **File Grouping**: Groups PublisherApp and SubscriberApp files by module
3. **GUI Display**: Shows selectable modules and files
4. **QoS Configuration**: Provides simple and advanced configuration modes
5. **Patch Application**: Calls `qos_settings_patcher.py` to apply changes

## Usage

### Launch GUI

```bash
cd scripts/py
python3 qos_settings_patcher_gui.py
```

### Via Shell Script

```bash
bash scripts/sh/patch_qos_settings.sh
```

## GUI Features

### Module Selection
- Checkbox list of all available modules
- Publisher/Subscriber file selection
- Scrollable interface for many modules

### Simple Mode
- History QoS policy selection only
- KEEP_LAST (with depth input)
- KEEP_ALL
- Other policies use safe defaults

### Advanced Mode
- Full QoS configuration for DataWriter
- Full QoS configuration for DataReader
- All supported QoS policies available

### Apply Button
- Applies QoS patches to selected files
- Shows progress and results
- Displays success/failure status

## Requirements

- Python 3.x
- tkinter library (usually included with Python)
- `qos_settings_patcher.py` module (must be in same directory)

## Integration

Launched by:
- `scripts/sh/patch_qos_settings.sh` - Shell script wrapper

## Notes

- Requires GUI environment (X11 on Linux, Windows GUI)
- Automatically detects available modules
- Provides visual feedback for all operations
- Safe to use: creates backups automatically

