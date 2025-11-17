# simple_dynamic_test.sh

## Overview

`simple_dynamic_test.sh` automatically discovers and tests all IDL modules by running their Publisher and Subscriber executables. It launches each module in separate terminal windows for easy monitoring.

## Purpose

- Automatically discovers all `*_idl_generated` modules
- Launches Publisher and Subscriber for each module
- Opens separate terminal windows for each process
- Provides easy testing of DDS communication

## How It Works

1. **Module Discovery**: Finds all `*_idl_generated` directories
2. **Executable Detection**: Finds `*main` executables in each module
3. **Process Launch**: Starts Publisher and Subscriber in separate terminals
4. **Terminal Selection**: Uses available terminal emulator (gnome-terminal, xterm, konsole, etc.)

## Usage

### Basic Usage

```bash
cd scripts/sh
bash simple_dynamic_test.sh
```

### From Project Root

```bash
bash scripts/sh/simple_dynamic_test.sh
```

## Terminal Emulators Supported

The script tries these terminals in order:
1. `gnome-terminal` (GNOME)
2. `xterm` (X11)
3. `konsole` (KDE)
4. `alacritty` (Alacritty)
5. `kitty` (Kitty)

## Process Launch

For each module:
- Launches Publisher: `./<Module>main publisher`
- Launches Subscriber: `./<Module>main subscriber`
- Each in separate terminal window

## Working Directory

Uses `build/` directory if it exists, otherwise uses `*_idl_generated` root.

## Requirements

- Bash shell
- Terminal emulator (one of the supported ones)
- IDL modules must be built first
- Executables must exist in build directories

## Integration

Can be used:
- After building modules
- For testing DDS communication
- For debugging publisher/subscriber issues

## Notes

- Automatically discovers all modules
- No manual configuration needed
- Each process runs in separate terminal
- Processes continue running until manually stopped
- Useful for testing multiple modules simultaneously

