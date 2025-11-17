# Secure DDS System

## Overview

The Secure DDS System provides comprehensive security for DDS communications using industry-standard Public Key Infrastructure (PKI) and encryption. It implements authentication, encryption, and optional access control to ensure secure, authenticated, and encrypted data exchange between DDS participants.

## Purpose

The secure DDS system enables:

- **Authentication**: Verify participant identity using X.509 certificates
- **Encryption**: Encrypt payload data using AES-GCM-GMAC
- **Access Control**: Optional governance and permissions (currently disabled)
- **PC-Specific Security**: Unique certificates per machine (hostname-based)
- **Certificate Management**: Automated certificate creation and renewal
- **Production-Ready Security**: Industry-standard security protocols

## Architecture

### Security Components

1. **Certificate Authority (CA)**
   - Root CA certificate and private key
   - Signs participant certificates
   - Central trust anchor

2. **Participant Certificates**
   - PC-specific certificates (one per hostname)
   - Signed by Root CA
   - Includes public key and identity information

3. **Private Keys**
   - Corresponding private keys for participant certificates
   - Stored securely per participant
   - Never shared or transmitted

4. **Security Policy Documents**
   - Governance XML: Defines security rules
   - Permissions XML: Defines access control rules
   - Signed documents (P7S format)

### Security Plugins

1. **Authentication Plugin**: `builtin.PKI-DH`
   - PKI-DH (Public Key Infrastructure - Diffie-Hellman)
   - X.509 certificate-based authentication
   - Mutual authentication between participants

2. **Encryption Plugin**: `builtin.AES-GCM-GMAC`
   - AES-GCM (Advanced Encryption Standard - Galois/Counter Mode)
   - GMAC (Galois Message Authentication Code)
   - Payload encryption and integrity

3. **Access Control Plugin**: `builtin.Access-Permissions` (optional)
   - Governance and permissions enforcement
   - Currently disabled for simplicity
   - Can be enabled for fine-grained access control

## How It Works

### 1. Certificate Infrastructure

#### Root CA Creation

The Root CA is created once per project:

**Location**: `secure_dds/CA/`

**Files Created**:
- `mainca_cert.pem` - Root CA certificate (public)
- `private/mainca_key.pem` - Root CA private key (secret)
- `maincaconf.cnf` - CA configuration file
- `serial` - Certificate serial number tracking
- `index.txt` - Certificate database

**Creation Process** (`certificate.py`):
1. Creates CA directory structure
2. Generates CA configuration file
3. Creates CA private key
4. Generates self-signed CA certificate
5. Initializes CA database files

#### Participant Certificate Creation

Each PC (identified by hostname) gets its own certificate:

**Location**: `secure_dds/participants/<hostname>/`

**Files Created**:
- `<hostname>_cert.pem` - Participant certificate (signed by CA)
- `<hostname>_key.pem` - Participant private key
- `<hostname>.csr` - Certificate Signing Request
- `security/governance.xml` - Governance document
- `security/permissions.xml` - Permissions document
- `security/governance.p7s` - Signed governance
- `security/permissions.p7s` - Signed permissions

**Creation Process**:
1. Detects hostname using `socket.gethostname()`
2. Creates participant directory
3. Generates private key
4. Creates Certificate Signing Request (CSR)
5. Signs certificate with Root CA
6. Generates security policy documents
7. Signs policy documents

### 2. Security Configuration

#### Participant QoS Configuration

Security is configured in DomainParticipantQos:

```cpp
DomainParticipantQos pqos = PARTICIPANT_QOS_DEFAULT;

// Authentication plugin
pqos.properties().properties().emplace_back(
    "dds.sec.auth.plugin",
    "builtin.PKI-DH"
);

// Certificate paths
pqos.properties().properties().emplace_back(
    "dds.sec.auth.builtin.PKI-DH.identity_ca",
    "file:///path/to/secure_dds/CA/mainca_cert.pem"
);

pqos.properties().properties().emplace_back(
    "dds.sec.auth.builtin.PKI-DH.identity_certificate",
    "file:///path/to/secure_dds/participants/<hostname>/<hostname>_cert.pem"
);

pqos.properties().properties().emplace_back(
    "dds.sec.auth.builtin.PKI-DH.private_key",
    "file:///path/to/secure_dds/participants/<hostname>/<hostname>_key.pem"
);

// Encryption plugin
pqos.properties().properties().emplace_back(
    "dds.sec.crypto.plugin",
    "builtin.AES-GCM-GMAC"
);

// Payload protection
pqos.properties().properties().emplace_back(
    "rtps.payload_protection",
    "ENCRYPT"
);
```

#### Dynamic Path Detection

Paths are detected dynamically:

1. **Project Root Detection**:
   - Walks up directory tree to find `secure_dds/` directory
   - Uses `DDS_ROOT` environment variable if set
   - Falls back to current directory

2. **Hostname Detection**:
   - Uses `gethostname()` system call
   - Falls back to "UNKNOWN_PC" if detection fails

3. **Path Construction**:
   - Constructs certificate paths relative to project root
   - Uses `file://` URI scheme for DDS compatibility
   - Handles Windows/Linux path differences

### 3. Authentication Process

#### PKI-DH Authentication Flow

1. **Participant Initialization**:
   - Participant loads its certificate and private key
   - Registers with DDS security framework

2. **Discovery Phase**:
   - Participants discover each other via DDS discovery
   - Exchange certificate information

3. **Authentication**:
   - Verify certificates against CA
   - Perform Diffie-Hellman key exchange
   - Establish authenticated session

4. **Session Establishment**:
   - Create secure session keys
   - Ready for encrypted communication

### 4. Encryption Process

#### AES-GCM-GMAC Encryption

1. **Key Derivation**:
   - Session keys derived from authentication
   - Unique keys per participant pair

2. **Payload Encryption**:
   - Encrypt DDS payload data using AES-GCM
   - Add authentication tag using GMAC
   - Transparent to application code

3. **Decryption**:
   - Decrypt payload at receiver
   - Verify integrity using GMAC tag
   - Deliver plaintext to application

### 5. Certificate Renewal

#### Automatic Renewal Logic

Certificates are automatically renewed if:

1. **Missing Certificates**: CA or participant certificates don't exist
2. **Expired Certificates**: Certificates created before last year's January 1st
3. **System Time Issues**: Fallback to 1-year age check if date calculation fails

**Renewal Process** (`setup.sh`):
1. Checks certificate existence
2. Calculates certificate age
3. Compares with renewal threshold
4. Triggers certificate recreation if needed

**Renewal Threshold**:
- Certificates created before January 1st of previous year
- Example: If current year is 2026, renew certificates created before 2025-01-01

## Technologies Used

### Core Technologies

- **OpenSSL**: Certificate generation and management
- **X.509 Certificates**: Industry-standard certificate format
- **PKI-DH**: Public Key Infrastructure with Diffie-Hellman
- **AES-GCM-GMAC**: Advanced encryption standard with authentication
- **Fast-DDS Security Plugins**: Built-in security plugins

### Certificate Format

- **PEM Format**: Base64-encoded certificates and keys
- **X.509 v3**: Certificate version 3 standard
- **RSA Keys**: RSA key pairs for certificates
- **SHA-256**: Hash algorithm for signatures

## Requirements

### System Requirements

- **OpenSSL**: Command-line tools and libraries
- **Python 3.x**: For certificate generation scripts
- **Fast-DDS**: With security plugins enabled
- **File System**: Write permissions for certificate storage

### Certificate Requirements

- **CA Certificate**: Must exist before creating participant certificates
- **Valid Hostname**: Hostname must be resolvable for certificate naming
- **File Permissions**: Appropriate permissions on certificate files
- **Path Accessibility**: Certificates must be accessible via file paths

## Usage

### Certificate Creation

#### Automatic Creation (Recommended)

Certificates are created automatically by:

**setup.sh**:
```bash
bash setup.sh
```

This script:
1. Checks for existing certificates
2. Validates certificate age
3. Creates certificates if needed or expired
4. Configures security in generated code

**certificate.py**:
```bash
python3 scripts/py/certificate.py
```

Standalone certificate generation.

#### Manual Creation

If needed, certificates can be created manually using OpenSSL:

```bash
# Create CA (one-time)
openssl req -new -x509 -keyout secure_dds/CA/private/mainca_key.pem \
    -out secure_dds/CA/mainca_cert.pem -days 365

# Create participant certificate
openssl genrsa -out secure_dds/participants/<hostname>/<hostname>_key.pem 2048
openssl req -new -key secure_dds/participants/<hostname>/<hostname>_key.pem \
    -out secure_dds/participants/<hostname>/<hostname>.csr
openssl ca -in secure_dds/participants/<hostname>/<hostname>.csr \
    -out secure_dds/participants/<hostname>/<hostname>_cert.pem
```

### Security Application

#### Automatic Application

Security is automatically applied by:

**security.py**:
```bash
python3 scripts/py/security.py
```

This script:
1. Finds all PublisherApp and SubscriberApp files
2. Injects security configuration code
3. Sets up certificate paths dynamically
4. Configures authentication and encryption

#### Manual Configuration

Security can be configured manually in code:

```cpp
DomainParticipantQos pqos = PARTICIPANT_QOS_DEFAULT;

// Add security properties (see configuration section above)
// ...

DomainParticipant* participant = factory->create_participant(
    domain_id, pqos
);
```

### Certificate Verification

#### Check Certificate Validity

```bash
# View CA certificate
openssl x509 -in secure_dds/CA/mainca_cert.pem -text -noout

# View participant certificate
openssl x509 -in secure_dds/participants/<hostname>/<hostname>_cert.pem -text -noout

# Verify certificate chain
openssl verify -CAfile secure_dds/CA/mainca_cert.pem \
    secure_dds/participants/<hostname>/<hostname>_cert.pem
```

## Folder Structure

```
secure_dds/
├── CA/                              # Certificate Authority
│   ├── mainca_cert.pem             # Root CA certificate (public)
│   ├── private/
│   │   └── mainca_key.pem          # Root CA private key (secret)
│   ├── maincaconf.cnf              # CA configuration
│   ├── serial                      # Certificate serial tracking
│   └── index.txt                   # Certificate database
├── appconf.cnf                     # Application configuration
└── participants/                   # Participant certificates
    └── <hostname>/                 # PC-specific directory
        ├── <hostname>_cert.pem     # Participant certificate
        ├── <hostname>_key.pem      # Participant private key
        ├── <hostname>.csr          # Certificate Signing Request
        └── security/
            ├── governance.xml      # Governance document
            ├── permissions.xml      # Permissions document
            ├── governance.p7s      # Signed governance
            └── permissions.p7s     # Signed permissions
```

## Security Configuration Details

### Authentication Properties

- **Plugin**: `builtin.PKI-DH`
- **Identity CA**: Root CA certificate path
- **Identity Certificate**: Participant certificate path
- **Private Key**: Participant private key path

### Encryption Properties

- **Plugin**: `builtin.AES-GCM-GMAC`
- **Payload Protection**: `ENCRYPT` (encrypts all payloads)

### Access Control (Optional)

- **Plugin**: `builtin.Access-Permissions`
- **Governance**: Governance document path
- **Permissions**: Permissions document path
- **Permissions CA**: CA certificate for permissions validation

**Note**: Access control is currently disabled for simplicity. Enable by adding access control properties and configuring governance/permissions.

## Integration Points

### With Setup System

- `setup.sh` checks and creates certificates automatically
- Certificate renewal logic integrated into setup process
- Security configuration applied during setup

### With Code Generation

- `security.py` patches generated code with security configuration
- Certificate paths injected dynamically
- Cross-platform path handling

### With Build System

- No special build requirements for security
- OpenSSL libraries linked automatically
- Security is runtime configuration

### With Monitoring System

- Monitor uses same security configuration
- PC-specific certificates for monitor
- Secure communication with publishers

## Troubleshooting

### Certificate Errors

**Problem**: Security initialization fails with certificate errors

**Solutions**:
1. **Check Certificate Existence**: Verify certificates exist at expected paths
2. **Verify Hostname**: Ensure hostname matches certificate directory name
3. **Check File Permissions**: Verify read permissions on certificate files
4. **Validate Certificate Chain**: Verify certificate is signed by CA
5. **Check Certificate Validity**: Ensure certificates are not expired

### Path Issues

**Problem**: Certificate paths not found or incorrect

**Solutions**:
1. **Verify Project Root**: Check that project root detection works
2. **Check Path Construction**: Verify path construction logic
3. **Test File Access**: Ensure files are accessible via constructed paths
4. **Windows/Linux Differences**: Check path separator handling
5. **Use Absolute Paths**: Try absolute paths if relative paths fail

### Authentication Failures

**Problem**: Participants cannot authenticate

**Solutions**:
1. **Verify CA Certificate**: Ensure all participants use same CA
2. **Check Certificate Validity**: Verify certificates are valid and not expired
3. **Verify Certificate Chain**: Ensure certificates are signed by CA
4. **Check Network**: Verify network connectivity for certificate exchange
5. **Review Security Logs**: Check DDS security logs for detailed errors

### Encryption Issues

**Problem**: Data not encrypted or decryption fails

**Solutions**:
1. **Verify Encryption Plugin**: Ensure encryption plugin is configured
2. **Check Payload Protection**: Verify `rtps.payload_protection` is set to `ENCRYPT`
3. **Verify Session Keys**: Ensure authentication succeeded (required for encryption)
4. **Check Plugin Compatibility**: Verify Fast-DDS version supports encryption
5. **Review Encryption Logs**: Check DDS logs for encryption errors

## Best Practices

### Certificate Management

1. **Secure Storage**: Protect private keys (never share or commit)
2. **Regular Renewal**: Renew certificates before expiration
3. **Backup**: Keep secure backups of CA and certificates
4. **Access Control**: Restrict access to certificate directories
5. **Documentation**: Document certificate creation and renewal procedures

### Security Configuration

1. **Always Use Security**: Enable security in production environments
2. **Test Security**: Test security configuration in isolated environment
3. **Monitor Security**: Monitor security logs for issues
4. **Update Regularly**: Keep Fast-DDS and OpenSSL updated
5. **Document Configuration**: Document security settings and rationale

### Development

1. **Test Without Security**: Develop and test without security first
2. **Enable Security Gradually**: Enable security incrementally
3. **Validate Certificates**: Verify certificates work before deployment
4. **Error Handling**: Implement proper error handling for security failures
5. **Logging**: Enable security logging for troubleshooting

## Operation Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              Certificate Authority (CA)                     │
│  secure_dds/CA/mainca_cert.pem                            │
│  - Root certificate                                        │
│  - Signs participant certificates                          │
└────────────────────┬────────────────────────────────────────┘
                     │ Signs
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Participant Certificates                            │
│  secure_dds/participants/<hostname>/                       │
│  ├── <hostname>_cert.pem  (signed by CA)                  │
│  └── <hostname>_key.pem    (private key)                   │
└────────────────────┬────────────────────────────────────────┘
                     │ Used in DDS QoS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              DDS Participant                                │
│  DomainParticipantQos:                                      │
│  - Authentication: PKI-DH                                   │
│  - Encryption: AES-GCM-GMAC                                 │
│  - Certificate paths configured                            │
└────────────────────┬────────────────────────────────────────┘
                     │ Secure DDS Communication
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Authenticated & Encrypted Data Exchange            │
│  - Mutual authentication                                    │
│  - Encrypted payloads                                       │
│  - Integrity verification                                   │
└─────────────────────────────────────────────────────────────┘
```

## Notes

- Security is transparent to application code (handled at DDS layer)
- Certificates are PC-specific (one per hostname)
- CA certificate is shared across all participants
- Private keys must be kept secret (never shared)
- Certificate renewal is automatic (based on creation date)
- Security can be enabled/disabled per participant
- Access control is optional (currently disabled for simplicity)
- The system uses industry-standard security protocols
- Security configuration is applied automatically by patching scripts
