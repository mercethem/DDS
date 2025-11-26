# setup_security_certificates.sh

## Overview

`setup_security_certificates.sh` sets up DDS security by creating certificates and applying security patches. It orchestrates the complete security setup process.

## Purpose

- Creates certificates if they don't exist
- Applies security patches to Publisher/Subscriber files
- Configures DDS security settings
- Ensures PC-specific certificate setup

## How It Works

1. **Portability Check**: Verifies project structure
2. **Python Detection**: Finds Python installation
3. **Certificate Creation**: Runs `generate_security_certificates.py` to create certificates
4. **Security Patching**: Runs `apply_security_settings.py` to apply security settings

## Usage

### Basic Usage

```bash
cd scripts/sh
bash setup_security_certificates.sh
```

### From Project Root

```bash
bash scripts/sh/setup_security_certificates.sh
```

## Execution Steps

1. **Certificate Check**: Checks if certificates exist
2. **Certificate Creation**: Creates Root CA and PC certificates if needed
3. **Security Application**: Applies security patches to all Publisher/Subscriber files

## Certificate Files Created

- `secure_dds/CA/mainca_cert.pem` - Root CA certificate
- `secure_dds/CA/private/mainca_key.pem` - Root CA private key
- `secure_dds/participants/<PC_NAME>/<PC_NAME>_cert.pem` - PC certificate
- `secure_dds/participants/<PC_NAME>/<PC_NAME>_key.pem` - PC private key
- Security policy files (governance.xml, permissions.xml, signed versions)

## Requirements

- Python 3.x
- OpenSSL installed
- Write permissions to `secure_dds/` directory
- IDL modules must be generated first

## Integration

This script is called by:
- `init/sh/project_setup.sh` - During security setup phase
- `run_complete_workflow.sh` - As STEP 4

## Notes

- Automatically detects PC name
- Creates certificates only if they don't exist
- Applies security to all Publisher/Subscriber files
- Cross-platform compatible

