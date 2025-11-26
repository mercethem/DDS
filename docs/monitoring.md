# Monitoring System

## Overview

The Monitoring System is a unified, multi-domain DDS subscriber application designed to monitor and display DDS data streams across multiple domains and topics simultaneously. It serves as the central data collection point for the DDS infrastructure, subscribing to all active topics and providing real-time data output for visualization and analysis.

## Purpose

The monitoring system provides:

- **Multi-Domain Monitoring**: Simultaneously monitors multiple DDS domains (default: 0-5, configurable)
- **Multi-Topic Subscription**: Subscribes to all topic types (CoreData variants, Intelligence, Messaging)
- **Real-Time Data Display**: Prints received samples in formatted, parseable format
- **Security Integration**: Full DDS security support (PKI-DH authentication, AES-GCM-GMAC encryption)
- **Process Integration**: Designed to integrate with demo dashboard via stdout parsing
- **Production-Ready**: Robust error handling and graceful shutdown

## Architecture

### Components

1. **monitor.cpp** - Main C++ application
   - Multi-domain participant management
   - Topic subscription and data reception
   - Security configuration
   - Output formatting

2. **run_monitoring.sh** - Launch script (located in `monitoring/run_monitoring/`)
   - Build verification and execution
   - Environment variable handling
   - Process management

3. **build_monitoring.sh** - Build script (located in `monitoring/build_monitoring/`)
   - CMake configuration
   - Dependency detection
   - Compilation and linking

4. **CMakeLists.txt** - Build configuration
   - Fast-DDS dependency management
   - Library linking
   - RPATH configuration for portability

### Key Features

- **Dynamic Domain Configuration**: Supports comma-separated and range syntax (e.g., "0-3,5")
- **PC-Specific Security**: Automatically detects hostname for certificate paths
- **Dynamic Path Detection**: Finds project root and certificates automatically
- **Thread-Safe Output**: Uses mutex for synchronized stdout output
- **Graceful Shutdown**: Handles SIGINT/SIGTERM for clean termination

## How It Works

### 1. Domain Configuration

The monitor accepts domain IDs through multiple methods (priority order):

1. **Command-Line Argument**: `./monitor "0,1,2"` or `./monitor "0-3"`
2. **Environment Variable**: `MONITOR_DOMAINS="0,1,2"`
3. **Default**: Domains 0-5 if not specified

**Domain Parsing Syntax:**
- **Comma-separated**: `"0,1,2"` → domains 0, 1, 2
- **Range**: `"0-3"` → domains 0, 1, 2, 3
- **Mixed**: `"0,2-4,6"` → domains 0, 2, 3, 4, 6

**Implementation:**
```cpp
std::vector<int> parse_domains_from_input(const std::string& input);
```

### 2. DDS Participant Creation

For each configured domain:

1. **Security Configuration**:
   - Creates DomainParticipantQos with security enabled
   - Configures authentication plugin: `builtin.PKI-DH`
   - Configures encryption plugin: `builtin.AES-GCM-GMAC`
   - Sets certificate paths dynamically

2. **Certificate Path Resolution**:
   - Detects project root (walks up directory tree)
   - Detects hostname using `gethostname()`
   - Constructs certificate paths:
     - CA: `secure_dds/CA/mainca_cert.pem`
     - Identity: `secure_dds/participants/<hostname>/<hostname>_cert.pem`
     - Private Key: `secure_dds/participants/<hostname>/<hostname>_key.pem`

3. **Participant Creation**:
   - Creates DomainParticipant for each domain
   - Sets participant name: `DDS_Monitor_participant`
   - Creates Subscriber for data reception

### 3. Topic Subscription

For each domain, the monitor subscribes to:

**Aircraft Topics (CoreData variants):**
- `CoreDataTopic` (CoreData module)
- `CoreData2Topic` (CoreData2 module)
- `CoreData3Topic` (CoreData3 module)
- `CoreData4Topic` (CoreData4 module)

**Intelligence Topic:**
- `IntelligenceTopic` (Intelligence module)

**Messaging Topic:**
- `MessagingTopic` (Messaging module)

**Subscription Process:**
1. Creates Topic for each type
2. Registers TypeSupport (PubSubTypes)
3. Creates DataReader with default QoS
4. Attaches listener for data reception

### 4. Data Reception and Processing

Each topic type has a dedicated listener class:

#### CoreDataMonitor

**Purpose**: Handles CoreData variant topics

**Data Extraction**:
- Position: latitude, longitude, altitude
- Time: time_seconds, time_nano_seconds
- Motion: speed_mps, orientation_degrees

**Output Format**:
```
[domain=0] TOPIC: aircraft coredata
Sample '1' RECEIVED
 - {latitude: 39.9334, longitude: 32.8597, altitude: 1500.0, time_seconds: 1730352000, time_nano_seconds: 500000000, speed_mps: 250.5, orientation_degrees: 45.0}
```

#### IntelligenceMonitor

**Purpose**: Handles Intelligence topic

**Data Extraction**:
- Vehicle status (battery, signal strength, system errors)
- Target detection (ID, type, location, confidence)
- Task assignment (command, location, parameters)

**Output Format**: Similar structure with intelligence-specific fields

#### MessagingMonitor

**Purpose**: Handles Messaging topic

**Data Extraction**:
- Status reports (sender, location, status)
- Target detection information
- Task command assignments

**Output Format**: Similar structure with messaging-specific fields

### 5. Output Format

The monitor prints data in a structured, parseable format:

**Format Structure:**
```
[domain=<ID>] TOPIC: <category> <subtype>
Sample '<count>' RECEIVED
 - {field1: value1, field2: value2, ...}
```

**Characteristics:**
- Domain ID in brackets for routing
- Topic category and subtype identification
- Sample counter for tracking
- JSON-like data structure for easy parsing

**Parsing by Demo Server:**
The demo server (`demo/server.js`) parses this output using regex patterns:
- Extracts domain ID
- Identifies topic type
- Parses data fields
- Emits WebSocket events

### 6. Security Integration

**Authentication:**
- Plugin: `builtin.PKI-DH`
- Uses X.509 certificates for identity verification
- CA certificate validates participant certificates

**Encryption:**
- Plugin: `builtin.AES-GCM-GMAC`
- Payload encryption enabled
- Transparent to application code

**Access Control:**
- Disabled (no governance/permissions required)
- Simplifies configuration while maintaining security

## Technologies Used

### Core Technologies

- **C++17**: Modern C++ standard
- **Fast-DDS**: DDS middleware implementation
- **Fast-CDR**: Serialization library
- **CMake**: Build system
- **OpenSSL**: Cryptographic library

### Dependencies

- **Generated IDL Libraries**: Static libraries from IDL modules
  - `libCoreData_lib.a`
  - `libIntelligence_lib.a`
  - `libMessaging_lib.a`

## Requirements

### Build Requirements

- **CMake**: Version 3.10 or higher
- **C++ Compiler**: GCC 7+, Clang 5+, or MSVC 2017+ (C++17 support)
- **Fast-DDS**: Installed and discoverable by CMake
- **Fast-CDR**: Installed and discoverable by CMake
- **OpenSSL**: Development libraries
- **Generated IDL Libraries**: Must be built first (`build_idl_modules.sh`)

### Runtime Requirements

- **Fast-DDS Runtime**: Shared libraries in library path
- **Fast-CDR Runtime**: Shared libraries in library path
- **OpenSSL Runtime**: Shared libraries in library path
- **DDS Certificates**: Valid certificates in `secure_dds/` directory
- **Network**: UDP multicast support (for DDS communication)

## Usage

### Building

#### Using build_monitoring.sh (Recommended)

```bash
cd monitoring/build_monitoring
bash build_monitoring.sh
```

**What it does:**
1. Creates `build/` directory in `monitoring/`
2. Detects Fast-DDS installation paths
3. Configures CMake
4. Builds monitor executable
5. Outputs to `monitoring/build/monitor`

#### Using CMake Directly

```bash
cd monitoring
mkdir -p build
cd build
cmake ..
make
```

**Or with parallel build:**
```bash
make -j$(nproc)
```

### Running

#### Basic Usage

```bash
cd monitoring/run_monitoring
bash run_monitoring.sh
```

Or directly:
```bash
cd monitoring
./build/monitor
```

#### Specify Domains

**Command-line argument:**
```bash
./build/monitor "0,1,2"
```

**Range syntax:**
```bash
./build/monitor "0-3"
```

**Mixed syntax:**
```bash
./build/monitor "0,2-4,6"
```

#### Environment Variable

```bash
MONITOR_DOMAINS="0,1,2" ./build/monitor
```

Or via run_monitoring.sh:
```bash
cd monitoring/run_monitoring
MONITOR_DOMAINS="0-3" bash run_monitoring.sh
```

### Integration with Demo Dashboard

The demo server can automatically start the monitor:

**Automatic Start:**
- Demo server detects monitor executable
- Starts monitor process automatically
- Parses monitor stdout output
- Forwards data to dashboard via WebSocket

**Manual Start:**
- Start monitor separately
- Demo server connects to existing monitor output
- Both processes can run independently

**Process Communication:**
```
Monitor (stdout) → Demo Server (stdin parsing) → WebSocket → Dashboard
```

## Security Configuration

<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> 9f27b6be (directory managemend upgraded, scripts renamed, docs updated)
### Certificate Structure

See `monitoring.mdd` for the complete certificate structure diagram.

<<<<<<< HEAD
=======
>>>>>>> 4094b194 (directory managemend upgraded, scripts renamed, docs updated)
>>>>>>> 9f27b6be (directory managemend upgraded, scripts renamed, docs updated)
### Certificate Requirements

- **CA Certificate**: Must exist and be valid
- **Participant Certificate**: PC-specific, signed by CA
- **Private Key**: Corresponds to participant certificate
- **Permissions**: Optional (access control disabled)

### Certificate Creation

Certificates are created automatically by:
- `init/sh/project_setup.sh` - During project setup
- `scripts/py/generate_security_certificates.py` - Standalone certificate generation
- `scripts/sh/setup_security_certificates.sh` - Security setup workflow

## Path Detection

### Project Root Detection

The monitor dynamically detects the project root:

**Method 1: Environment Variable**
```cpp
if (const char* env_root = std::getenv("DDS_ROOT")) {
    // Use DDS_ROOT if set
}
```

**Method 2: Directory Walk**
```cpp
// Walk up from current directory
// Look for secure_dds/ and IDL/ directories
// Maximum 6 levels up
```

**Method 3: Current Directory**
```cpp
// Fallback to current directory
```

### Hostname Detection

```cpp
char hostname[256] = {0};
gethostname(hostname, sizeof(hostname) - 1);
// Use hostname for certificate paths
```

## Output Parsing

### Demo Server Integration

The demo server parses monitor output using regex:

**Pattern Matching:**
- Domain: `\[domain=(\d+)\]`
- Topic: `TOPIC: (\w+) (\w+)`
- Data: `\{([^}]+)\}`

**Data Extraction:**
- Parses field-value pairs
- Maps to JavaScript objects
- Emits WebSocket events

### Custom Parsing

Monitor output can be parsed by:
- Custom scripts (grep, awk, sed)
- Log analysis tools
- Monitoring systems
- Custom applications

## Troubleshooting

### Monitor Not Receiving Data

**Symptoms**: Monitor runs but shows no samples

**Solutions**:
1. **Check Domain IDs**: Ensure publishers use matching domain IDs
2. **Verify Security**: Certificates must exist and be valid
3. **Check Topics**: Topic names must match exactly
4. **Network Issues**: DDS uses UDP multicast (check firewall)
5. **Publisher Status**: Verify publishers are running and sending data

### Build Errors

**Symptoms**: CMake or compilation fails

**Solutions**:
1. **Missing Fast-DDS**: Install Fast-DDS libraries
2. **Missing IDL Libraries**: Build IDL modules first (`build_idl_modules.sh`)
3. **CMake Errors**: Check `CMAKE_PREFIX_PATH` for Fast-DDS location
4. **Compiler Issues**: Verify C++17 support
5. **Library Paths**: Check library paths in CMakeLists.txt

### Certificate Errors

**Symptoms**: Security initialization fails

**Solutions**:
1. **Missing Certificates**: Run `generate_security_certificates.py` to create certificates
2. **Wrong Hostname**: Certificates are PC-specific, ensure hostname matches
3. **Path Issues**: Check `secure_dds/participants/<hostname>/` exists
4. **Certificate Validity**: Verify certificates are not expired
5. **Permissions**: Check file permissions on certificate files

### Domain Configuration Issues

**Symptoms**: Monitor doesn't subscribe to expected domains

**Solutions**:
1. **Check Domain Syntax**: Verify domain specification format
2. **Verify Parsing**: Check parsed domain list matches expectations
3. **Domain Range**: Ensure domain IDs are within valid range (0-232)
4. **Participant Creation**: Check for participant creation errors

## Best Practices

### Domain Configuration

1. **Use Environment Variables**: Prefer `MONITOR_DOMAINS` for configuration
2. **Document Domains**: Document which domains are used in your system
3. **Domain Isolation**: Use different domains for different subsystems
4. **Range Syntax**: Use range syntax for consecutive domains

### Security

1. **Certificate Management**: Keep certificates up to date
2. **Hostname Consistency**: Ensure hostname matches certificate directory
3. **Certificate Renewal**: Renew certificates before expiration
4. **Security Testing**: Test security configuration in isolated environment

### Performance

1. **Domain Limits**: Don't monitor unnecessary domains
2. **QoS Configuration**: Adjust QoS for performance if needed
3. **Output Buffering**: Consider output buffering for high-frequency data
4. **Resource Monitoring**: Monitor CPU and memory usage

## Project Structure

See `monitoring.mdd` for the complete project structure and operation diagrams.

## Notes

- The monitor runs continuously until stopped (Ctrl+C or SIGTERM)
- Multiple monitor instances can run simultaneously on different domains
- Output is thread-safe (uses mutex for stdout synchronization)
- Supports graceful shutdown via signal handling
- Designed for production use with robust error handling
- Integrates seamlessly with demo dashboard via stdout parsing
- Security is transparent to the application (handled at DDS layer)
