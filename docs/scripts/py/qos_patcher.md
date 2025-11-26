# qos_settings_patcher.py

## Overview

`qos_settings_patcher.py` applies Quality of Service (QoS) settings to DDS DataWriter and DataReader configurations. It patches PublisherApp and SubscriberApp files with QoS policies based on user selection.

## Purpose

- Applies QoS policies to DataWriter/DataReader
- Supports History QoS policy selection (KEEP_LAST, KEEP_ALL)
- Configures reliability, durability, liveliness, and other QoS settings
- Ensures Fast-DDS QoS compatibility

## How It Works

1. **File Discovery**: Finds all `*PublisherApp.cxx` and `*SubscriberApp.cxx` files
2. **QoS Configuration**: Applies selected QoS policies
3. **Code Injection**: Injects QoS configuration code into writer/reader creation
4. **Validation**: Validates QoS settings against Fast-DDS standards

## Usage

### Basic Usage (CLI)

```bash
cd scripts/py
python3 qos_settings_patcher.py
```

### GUI Version

```bash
python3 qos_settings_patcher_gui.py
```

Or via shell script:
```bash
bash scripts/sh/patch_qos_settings.sh
```

## QoS Policies Supported

- **Reliability**: RELIABLE, BEST_EFFORT
- **Durability**: VOLATILE, TRANSIENT_LOCAL
- **History**: KEEP_LAST, KEEP_ALL
- **Liveliness**: AUTOMATIC, MANUAL_BY_TOPIC, MANUAL_BY_PARTICIPANT
- **Destination Order**: BY_RECEPTION_TIMESTAMP, BY_SOURCE_TIMESTAMP

## Simple Mode

User selects only History QoS policy:
- KEEP_LAST (with depth)
- KEEP_ALL

Other policies use safe defaults.

## Advanced Mode

User can configure all QoS policies for:
- DataWriter QoS
- DataReader QoS

## Generated Code

Injects QoS configuration like:
```cpp
DataWriterQos wqos = PUBLISHER_QOS_DEFAULT;
wqos.reliability().kind = RELIABLE_RELIABILITY_QOS;
wqos.durability().kind = TRANSIENT_LOCAL_DURABILITY_QOS;
wqos.history().kind = KEEP_LAST_HISTORY_QOS;
wqos.history().depth = 10;
// ... more QoS settings ...
```

## Output Files

- Modified `*PublisherApp.cxx` and `*SubscriberApp.cxx` files
- Backup files created before modification

## Requirements

- Python 3.x
- tkinter (for GUI version)
- Fast-DDS QoS knowledge (for advanced mode)

## Integration

This script is called by:
- `scripts/sh/patch_qos_settings.sh` - GUI launcher
- Can be used standalone for CLI mode

## Notes

- Idempotent: safe to run multiple times
- Uses markers to identify injection points
- Validates QoS settings before applying
- Creates backups before modification

