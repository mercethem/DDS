# certificate.py

## Overview

`certificate.py` is a Secure DDS Certificate Manager that creates and manages PC-specific PKI (Public Key Infrastructure) certificates for DDS security. It automatically detects the PC name and creates unique certificates for each machine.

## Purpose

- Creates Root CA (Certificate Authority) certificates
- Generates PC-specific participant certificates
- Signs DDS security policy documents (governance.xml, permissions.xml)
- Manages certificate lifecycle and renewal

## How It Works

1. **PC Name Detection**: Automatically detects the hostname using `socket.gethostname()`
2. **Project Root Detection**: Dynamically finds the project root directory
3. **Certificate Creation**:
   - Creates Root CA if it doesn't exist
   - Generates PC-specific private keys and certificates
   - Signs security policy documents with the CA
4. **File Structure**: Creates certificates in `secure_dds/participants/<PC_NAME>/`

## Usage

### Basic Usage

```bash
cd scripts/py
python3 certificate.py
```

### From Project Root

```bash
python3 scripts/py/certificate.py
```

### Via Setup Script

The certificate creation is automatically handled by `setup.sh` during initial setup.

## Output Files

### Root CA Files
- `secure_dds/CA/mainca_cert.pem` - Root CA certificate
- `secure_dds/CA/private/mainca_key.pem` - Root CA private key
- `secure_dds/CA/maincaconf.cnf` - CA configuration file
- `secure_dds/CA/serial` - CA serial number file
- `secure_dds/CA/index.txt` - CA database file

### PC-Specific Files
- `secure_dds/participants/<PC_NAME>/<PC_NAME>_key.pem` - Private key
- `secure_dds/participants/<PC_NAME>/<PC_NAME>_cert.pem` - Certificate (signed by CA)
- `secure_dds/participants/<PC_NAME>/<PC_NAME>.csr` - Certificate Signing Request
- `secure_dds/participants/<PC_NAME>/security/governance.xml` - DDS governance rules
- `secure_dds/participants/<PC_NAME>/security/permissions.xml` - DDS permissions
- `secure_dds/participants/<PC_NAME>/security/governance.p7s` - Signed governance
- `secure_dds/participants/<PC_NAME>/security/permissions.p7s` - Signed permissions

## Certificate Renewal

Certificates are automatically renewed if:
- They don't exist
- They were created before January 1st of the previous year
- System time is incorrect (fallback to 1-year check)

## Requirements

- OpenSSL must be installed and available in PATH
- Python 3.x
- Write permissions to `secure_dds/` directory

## Error Handling

- Automatically creates necessary directories if they don't exist
- Validates OpenSSL availability before proceeding
- Provides detailed error messages if certificate creation fails

## Integration

This script is called by:
- `setup.sh` - During initial project setup
- `scripts/sh/dynamic_security_certificate.sh` - For security setup workflow

## Notes

- Certificates are PC-specific and should not be shared between machines
- The Root CA is shared across all participants
- Certificate files use PEM format (base64 encoded)

