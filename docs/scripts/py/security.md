# security.py

## Overview

`security.py` applies DDS security settings to C++ Publisher and Subscriber applications. It configures authentication (PKI-DH), encryption (AES-GCM-GMAC), and access control using PC-specific certificates.

## Purpose

- Applies DDS security configuration to participant QoS
- Uses PC-specific certificates from `secure_dds/participants/<PC_NAME>/`
- Configures authentication, encryption, and access control plugins
- Cross-platform path handling (Windows/Linux)

## How It Works

1. **PC Detection**: Automatically detects PC name using hostname
2. **Path Detection**: Dynamically finds project root and certificate paths
3. **File Discovery**: Finds all `*PublisherApp.cxx` and `*SubscriberApp.cxx` files
4. **Code Injection**: Injects security configuration code into participant creation
5. **Path Escaping**: Handles Windows/Linux path differences for C++ code

## Usage

### Basic Usage

```bash
cd scripts/py
python3 security.py
```

### From Project Root

```bash
python3 scripts/py/security.py
```

### Via Shell Script

```bash
bash scripts/sh/dynamic_security_certificate.sh
```

## Security Configuration

The script configures:
- **Authentication**: `builtin.PKI-DH` plugin
- **Encryption**: `builtin.AES-GCM-GMAC` plugin
- **Access Control**: `builtin.Access-Permissions` plugin (optional)

## Certificate Paths

Uses PC-specific certificates:
- CA Certificate: `secure_dds/CA/mainca_cert.pem`
- Participant Certificate: `secure_dds/participants/<PC_NAME>/<PC_NAME>_cert.pem`
- Private Key: `secure_dds/participants/<PC_NAME>/<PC_NAME>_key.pem`
- Governance: `secure_dds/participants/<PC_NAME>/security/governance.xml`
- Permissions: `secure_dds/participants/<PC_NAME>/security/permissions.p7s`

## Generated Code

Injects security configuration like:
```cpp
DomainParticipantQos pqos = PARTICIPANT_QOS_DEFAULT;
pqos.properties().properties().emplace_back("dds.sec.auth.plugin", "builtin.PKI-DH");
pqos.properties().properties().emplace_back("dds.sec.crypto.plugin", "builtin.AES-GCM-GMAC");
pqos.properties().properties().emplace_back("dds.sec.auth.builtin.PKI-DH.identity_ca", "file://.../CA/mainca_cert.pem");
// ... more security properties ...
```

## Requirements

- Python 3.x
- Certificates must exist (created by `certificate.py`)
- Read access to `secure_dds/` directory
- Write access to `IDL/*_idl_generated/` directories

## Integration

This script is called by:
- `setup.sh` - During security setup phase
- `scripts/sh/dynamic_security_certificate.sh` - Security workflow
- `scripts/sh/dynamic_ALL.sh` - Complete workflow

## Notes

- Cross-platform: handles Windows and Linux path differences
- Idempotent: safe to run multiple times (uses markers)
- Creates backups before modification
- Detects and replaces existing hardcoded security paths

