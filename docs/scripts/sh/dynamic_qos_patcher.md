# dynamic_qos_patcher.sh

## Overview

`dynamic_qos_patcher.sh` launches the QoS Patcher GUI application. It detects Python and starts the graphical interface for configuring QoS settings.

## Purpose

- Launches QoS Patcher GUI
- Detects Python installation dynamically
- Provides easy access to QoS configuration
- Wrapper script for `qos_patcher_gui.py`

## How It Works

1. **Python Detection**: Runs `dynamic_finder.sh` to find Python
2. **File Check**: Verifies `qos_patcher_gui.py` exists
3. **GUI Launch**: Starts the GUI application
4. **Status Report**: Shows exit status

## Usage

### Basic Usage

```bash
cd scripts/sh
bash dynamic_qos_patcher.sh
```

### From Project Root

```bash
bash scripts/sh/dynamic_qos_patcher.sh
```

## GUI Features

The GUI allows:
- Module selection (checkboxes)
- Publisher/Subscriber file selection
- Simple mode: History QoS only
- Advanced mode: Full QoS configuration
- Visual application of patches

## Requirements

- Python 3.x
- tkinter library (for GUI)
- `qos_patcher_gui.py` must exist
- GUI environment (X11 on Linux)

## Integration

Standalone script, can be run:
- After IDL generation
- Before or after building
- Anytime QoS configuration is needed

## Notes

- Requires GUI environment
- Automatically detects Python
- Provides user-friendly interface
- Safe to use: creates backups automatically

