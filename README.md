# DDS Project - Data Distribution Service Implementation

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Project Setup](#project-setup)
5. [Running the System](#running-the-system)
6. [Project Structure](#project-structure)
7. [Troubleshooting](#troubleshooting)
8. [Additional Documentation](#additional-documentation)

<a id="project-overview"></a>
## Project Overview

This project is a comprehensive Data Distribution Service (DDS) implementation using Fast-DDS middleware. It provides a complete solution for secure, real-time data distribution across multiple domains with support for publishers, subscribers, monitoring, and web-based visualization.

The system includes:

- IDL-based type definitions and code generation
- Secure DDS communication with PKI authentication and encryption
- Multi-domain support for topic isolation
- Real-time monitoring and data collection
- Web-based dashboard for visualization
- Scenario-based testing with JSON data injection
- Cross-platform portability

<a id="system-requirements"></a>
## System Requirements

### Operating System

- Linux (Ubuntu 20.04 or higher recommended, Debian-based distributions supported)
- Windows (with WSL 2 recommended for Linux compatibility)
- macOS (with manual Fast-DDS installation)

### Hardware Requirements

- CPU: Multi-core processor (2+ cores recommended)
- RAM: Minimum 4GB (8GB+ recommended for development)
- Disk Space: Minimum 2GB free space
- Network: Ethernet or WiFi connection (UDP multicast support required)

### Software Requirements

#### Essential Tools

- Bash shell (version 4.0 or higher)
- Git (for cloning the repository)
- sudo access (for package installation)

#### Build Tools

- CMake version 3.10 or higher
- C++ compiler with C++17 support:
  - GCC 7.0 or higher (Linux)
  - Clang 5.0 or higher (Linux/macOS)
  - MSVC 2017 or higher (Windows)
- Make or Ninja build system

#### Runtime Dependencies

- Fast-DDS libraries (libfastdds-dev)
- Fast-CDR libraries (libfastcdr-dev)
- OpenSSL development libraries (libssl-dev)
- Standard C++ runtime libraries

#### Development Tools

- Python 3.6 or higher (Python 3.8+ recommended)
- Java JDK 11 or higher (for fastddsgen)
- Node.js 14.0 or higher (for demo dashboard)
- npm 6.0 or higher (comes with Node.js)

#### Additional Libraries

- libtinyxml2-dev
- libfoonathan-memory-dev
- libasio-dev
- libboost-dev
- python3-tk (for QoS patcher GUI)

### Network Requirements

- UDP multicast support (required for DDS communication)
- Firewall configuration to allow UDP multicast traffic
- Internet connection (for map tiles in demo dashboard, optional)

<a id="installation"></a>
## Installation

### Step 1: Clone the Repository

Clone the project repository to your local machine:

```bash
git clone <repository-url>
cd DDS
```

Replace `<repository-url>` with the actual repository URL.

### Step 2: Install System Dependencies

#### For Ubuntu/Debian Systems

Run the automated dependency installer:

```bash
bash init/sh/install_system_dependencies.sh
```

This script will:
- Update system packages
- Install build tools (CMake, GCC, Make)
- Install Python 3 and Java JDK
- Install required libraries (OpenSSL, Fast-DDS, etc.)
- Configure environment variables

! IMPORTANT: Do not run the installer script as root. It will request sudo privileges automatically when needed.

#### Manual Installation (Alternative)

If the automated installer does not work or you prefer manual installation:

```bash
# Update system packages
sudo apt update

# Install build tools
sudo apt install -y build-essential cmake git pkg-config curl wget unzip

# Install Python and Java
sudo apt install -y python3 python3-pip python3-tk python3-dev openjdk-11-jdk

# Install library dependencies
sudo apt install -y libssl-dev libtinyxml2-dev libfoonathan-memory-dev libasio-dev libboost-dev

# Install Fast-DDS (Ubuntu 20.04+)
sudo apt install -y libfastcdr-dev libfastdds-dev fastddsgen

# Configure environment variables
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Update library cache
sudo ldconfig
```

#### For Other Linux Distributions

Install equivalent packages using your distribution's package manager. Fast-DDS may need to be built from source if packages are not available.

#### For Windows

Install dependencies manually:
- Install Visual Studio 2017 or higher with C++ support
- Install CMake
- Install Python 3
- Install Java JDK 11
- Build Fast-DDS from source or use pre-built binaries
- Install Node.js

### Step 3: Verify Installation

Verify that all required tools are installed:

```bash
# Check CMake
cmake --version

# Check C++ compiler
g++ --version

# Check Python
python3 --version

# Check Java
java -version

# Check Fast-DDS generator
fastddsgen -version

# Check Node.js (for demo)
node --version
npm --version
```

All commands should return version information without errors.

! CRITICAL: If any tool is missing or shows an error, installation is incomplete. Resolve missing dependencies before proceeding.

### Step 4: Configure Environment Variables

Add environment variables to your shell configuration file:

```bash
# Add to ~/.bashrc (Linux) or ~/.zshrc (macOS)
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
```

Reload your shell configuration:

```bash
source ~/.bashrc
```

Or restart your terminal.

<a id="project-setup"></a>
## Project Setup

After installing dependencies, you must set up the project. The setup process configures certificates, generates code, applies patches, and builds executables.

### Automated Setup (Recommended)

Run the automated setup script:

```bash
bash init/sh/project_setup.sh
```

This script performs all setup steps automatically:
- Runs the complete DDS workflow
- Creates security certificates
- Generates IDL code
- Applies code patches
- Builds all IDL modules
- Builds monitoring application
- Verifies setup completion

! IMPORTANT: The setup script must be run from the project root directory. It will take several minutes to complete depending on your system performance.

### Manual Setup (Step by Step)

If you prefer manual setup or need to troubleshoot, follow these steps in order:

#### Step 1: Environment Setup

Configure the project environment and detect tools:

```bash
cd scripts/sh
bash setup_environment.sh
```

This creates environment configuration files (`export_dds_environment.sh` and `setup_dds_aliases.sh`) in the `init/sh` directory.

#### Step 2: IDL Code Generation

Generate C++ code from IDL files:

```bash
cd scripts/sh
bash generate_idl_code.sh
```

This script:
- Scans all IDL files in the `IDL/` directory
- Runs fastddsgen to generate C++ code
- Creates `*_idl_generated/` directories for each module
- Downloads JSON library if missing

! CRITICAL: IDL generation must complete successfully before proceeding. Check for errors in the output.

#### Step 3: Update Domain IDs

Update domain IDs in generated code based on IDL file comments:

```bash
cd scripts/sh
bash update_domain_ids.sh
```

This ensures that generated applications use the correct DDS domain IDs specified in IDL files.

#### Step 4: Security Setup

Create security certificates and apply security configuration:

```bash
cd scripts/sh
bash setup_security_certificates.sh
```

This script:
- Creates Root CA certificate if missing
- Creates PC-specific participant certificates
- Generates security policy documents
- Applies security patches to generated code

! IMPORTANT: Certificates are PC-specific based on hostname. Each machine needs its own certificates.

#### Step 5: Apply Code Patches

Apply code enhancements in the correct order:

**5a. IDL Patcher** (creates default data blocks):

```bash
python3 scripts/py/idl_default_data_patcher.py
```

**5b. JSON Patcher** (replaces blocks with JSON reading):

```bash
python3 scripts/py/json_reading_patcher.py
```

! CRITICAL: Patches must be applied in this exact order. Running JSON patcher before IDL patcher will fail.

**5c. Security Patcher** (adds security configuration):

```bash
python3 scripts/py/apply_security_settings.py
```

**5d. Clean Duplicates** (removes duplicate code blocks):

```bash
python3 scripts/py/clean_duplicate_code.py
```

**5e. CMake Portability Fix** (makes CMake files portable):

```bash
python3 scripts/py/fix_cmake_rpath.py
```

#### Step 6: Build IDL Modules

Build all IDL modules:

```bash
cd scripts/sh
bash build_idl_modules.sh
```

This script:
- Finds all `*_idl_generated/` directories
- Configures CMake for each module
- Builds static libraries and executables
- Reports build results

Build output is placed in `IDL/<Module>_idl_generated/build/` directories.

#### Step 7: Build Monitoring System

Build the unified monitoring application:

```bash
cd monitoring/build_monitoring
bash build_monitoring.sh
```

This creates the monitor executable at `monitoring/build/monitor`.

#### Step 8: Setup Demo Dashboard

Install Node.js dependencies for the demo dashboard:

```bash
cd demo/build_demo
bash build_demo.sh
```

Or manually:

```bash
cd demo
npm install
```

This installs Express, Socket.IO, and other required packages.

### Verification

After setup, verify that everything is configured correctly:

```bash
# Check for generated code
ls IDL/*_idl_generated/

# Check for certificates
ls secure_dds/CA/mainca_cert.pem
ls secure_dds/participants/$(hostname)/$(hostname)_cert.pem

# Check for built executables
ls IDL/CoreData_idl_generated/build/CoreDatamain
ls monitoring/build/monitor

# Check demo dependencies
ls demo/node_modules/
```

All checks should show files exist. If any are missing, review the setup steps and check for errors.

<a id="running-the-system"></a>
## Running the System

### Running Publishers

Publishers send data via DDS topics. Each IDL module has its own publisher executable.

#### Basic Publisher Execution

Navigate to the module's build directory and run:

```bash
cd IDL/CoreData_idl_generated/build
./CoreDatamain publisher
```

Replace `CoreData` with the desired module name (CoreData2, CoreData3, CoreData4, Intelligence, Messaging).

#### Publisher Options

Publishers run continuously until stopped (Ctrl+C). They will:
- Connect to the DDS domain specified in the IDL file
- Use security certificates for authentication
- Read data from JSON scenario files (if JSON patcher was applied)
- Publish samples at regular intervals

! IMPORTANT: Publishers must use the same domain ID as subscribers to communicate. Domain IDs are specified in IDL files with `//domain=X` comments.

### Running Subscribers

Subscribers receive data from DDS topics.

#### Basic Subscriber Execution

```bash
cd IDL/CoreData_idl_generated/build
./CoreDatamain subscriber
```

Subscribers will:
- Connect to the DDS domain
- Subscribe to the topic
- Receive and display data samples
- Run until stopped (Ctrl+C)

### Running the Unified Monitor

The unified monitor subscribes to all topics across multiple domains:

```bash
cd monitoring/run_monitoring
bash run_monitoring.sh
```

Or directly:

```bash
./monitoring/build/monitor
```

#### Monitor Domain Configuration

Specify domains to monitor:

```bash
# Comma-separated domains
./monitoring/build/monitor "0,1,2"

# Range syntax
./monitoring/build/monitor "0-3"

# Mixed syntax
./monitoring/build/monitor "0,2-4,6"

# Environment variable
MONITOR_DOMAINS="0,1,2" ./monitoring/build/monitor
```

Default behavior monitors domains 0-5 if no specification is provided.

### Running the Demo Dashboard

The demo dashboard provides web-based visualization of DDS data.

#### Start the Dashboard Server

```bash
cd demo/run_demo
bash run_demo.sh
```

Or directly:

```bash
cd demo
node server.js
```

The server starts on port 3000 by default.

#### Access the Dashboard

Open a web browser and navigate to:

```
http://localhost:3000
```

The dashboard will display:
- Interactive map with aircraft positions
- Real-time data panels
- Intelligence and messaging information
- System status indicators

#### Dashboard Configuration

Configure the dashboard using environment variables:

```bash
# Change server port
PORT=8080 node demo/server.js

# Specify monitor domains
MONITOR_DOMAINS="0,1,2" node demo/server.js

# Disable DDS-only mode (enable simulation)
DDS_ONLY=0 node demo/server.js
```

#### Starting Publishers for Dashboard

After starting the dashboard, start publishers in separate terminals:

```bash
# Terminal 1: CoreData Publisher
cd IDL/CoreData_idl_generated/build
./CoreDatamain publisher

# Terminal 2: Intelligence Publisher
cd IDL/Intelligence_idl_generated/build
./Intelligencemain publisher

# Terminal 3: Messaging Publisher
cd IDL/Messaging_idl_generated/build
./Messagingmain publisher
```

Or use the unified monitor:

```bash
cd monitoring/run_monitoring
bash run_monitoring.sh
```

The dashboard will automatically parse monitor output and display data.

! IMPORTANT: The dashboard requires an internet connection for map tiles. If maps do not load, check your internet connection and firewall settings.

### Complete System Workflow

For a complete system demonstration:

1. Start the demo dashboard server:
   ```bash
   cd demo/run_demo
   bash run_demo.sh
   ```

2. In separate terminals, start publishers:
   ```bash
   # Terminal 1
   cd IDL/CoreData_idl_generated/build
   ./CoreDatamain publisher
   
   # Terminal 2
   cd IDL/Intelligence_idl_generated/build
   ./Intelligencemain publisher
   
   # Terminal 3
   cd IDL/Messaging_idl_generated/build
   ./Messagingmain publisher
   ```

3. Access the dashboard in your browser:
   ```
   http://localhost:3000
   ```

4. Observe real-time data visualization on the dashboard.

<a id="project-structure"></a>
## Project Structure

Understanding the project structure helps with navigation and troubleshooting.

See `README.mdd` for the complete directory structure diagram.

<a id="troubleshooting"></a>
## Troubleshooting

### Common Issues and Solutions

#### Setup Fails with Certificate Errors

**Problem**: Certificate creation fails during setup.

**Solution**:
1. Verify OpenSSL is installed: `openssl version`
2. Check write permissions on `secure_dds/` directory
3. Ensure hostname is resolvable: `hostname`
4. Manually create certificates: `python3 scripts/py/generate_security_certificates.py` or run `bash init/sh/project_setup.sh`

#### IDL Generation Fails

**Problem**: fastddsgen fails or produces errors.

**Solution**:
1. Verify Java is installed: `java -version`
2. Check fastddsgen is in PATH: `which fastddsgen`
3. Verify IDL file syntax (check for errors)
4. Check Java version compatibility (JDK 11+ required)
5. Review fastddsgen output for specific error messages

#### Build Failures

**Problem**: CMake or compilation fails.

**Solution**:
1. Verify Fast-DDS is installed: `pkg-config --modversion fastdds`
2. Check CMake version: `cmake --version` (3.10+ required)
3. Verify compiler supports C++17: `g++ -std=c++17 --version`
4. Check library paths: `echo $LD_LIBRARY_PATH`
5. Clean build directories and rebuild: `rm -rf IDL/*/build && bash scripts/sh/build_idl_modules.sh`

#### Publishers and Subscribers Don't Communicate

**Problem**: No data exchange between publishers and subscribers.

**Solution**:
1. Verify domain IDs match (check IDL files and generated code)
2. Check security certificates exist and are valid
3. Verify topic names match exactly
4. Check network connectivity (DDS uses UDP multicast)
5. Review firewall settings (UDP multicast must be allowed)
6. Check DDS logs for connection errors

#### Demo Dashboard Shows No Data

**Problem**: Dashboard loads but displays no data.

**Solution**:
1. Verify publishers are running and sending data
2. Check monitor is receiving data (check stdout)
3. Verify WebSocket connection (check browser console)
4. Ensure domain IDs match between publishers and monitor
5. Check server logs for parsing errors
6. Verify internet connection for map tiles

#### Certificate Verification Fails

**Problem**: Security initialization fails with certificate errors.

**Solution**:
1. Verify certificates exist: `ls secure_dds/CA/mainca_cert.pem`
2. Check hostname matches certificate directory: `hostname`
3. Verify certificate validity: `openssl x509 -in secure_dds/participants/$(hostname)/$(hostname)_cert.pem -text -noout`
4. Recreate certificates if needed: `python3 scripts/py/generate_security_certificates.py`
5. Check file permissions on certificate files

#### Port Already in Use

**Problem**: Demo dashboard fails to start because port 3000 is in use.

**Solution**:
1. Find process using port: `lsof -i :3000` or `netstat -tulpn | grep 3000`
2. Kill the process or use a different port: `PORT=8080 node demo/server.js`

#### Python Script Errors

**Problem**: Python patching scripts fail with errors.

**Solution**:
1. Verify Python 3 is installed: `python3 --version`
2. Check script permissions: `ls -l scripts/py/*.py`
3. Verify required Python modules are available
4. Check script execution order (IDL patcher before JSON patcher)
5. Review error messages for specific issues

### Getting Help

If you encounter issues not covered here:

1. Check the detailed documentation in the `docs/` directory
2. Review script documentation in `docs/scripts/`
3. Check error messages carefully for specific guidance
4. Verify all requirements are met
5. Review system logs for additional information

<a id="additional-documentation"></a>
## Additional Documentation

Comprehensive documentation is available in the `docs/` directory:

- **docs/demo.md**: Complete demo dashboard documentation
- **docs/IDL.md**: IDL system and code generation documentation
- **docs/monitoring.md**: Monitoring system documentation
- **docs/scenarios.md**: Scenario-based testing documentation
- **docs/secure_dds.md**: Security system documentation
- **docs/scripts/**: Individual script documentation

Each documentation file provides detailed information about its respective component, including architecture, usage, configuration, and troubleshooting.

## License

See the LICENSE file for license information.

## Support

For issues, questions, or contributions, please refer to the project repository or contact the development team.

