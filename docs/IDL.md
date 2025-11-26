# IDL (Interface Definition Language) System

## Overview

The IDL system is the foundation of the DDS project, defining data types and generating C++ code for publishers and subscribers. It uses the OMG IDL (Object Management Group Interface Definition Language) standard to define data structures that are then processed by Fast-DDS generator (`fastddsgen`) to create type-safe C++ code.

## Purpose

The IDL system serves multiple critical functions:

- **Type Definition**: Defines data structures using industry-standard IDL syntax
- **Code Generation**: Automatically generates C++ types, serialization code, and sample applications
- **Type Safety**: Ensures type safety across distributed systems
- **Cross-Platform Compatibility**: Generates platform-independent code
- **DDS Integration**: Creates DDS-compatible types with PubSubTypes for Fast-DDS

## Architecture

### IDL File Structure

Each IDL module follows a consistent structure:

```idl
//domain=<DOMAIN_ID>
module <ModuleName> {
    struct <StructName> {
        // Field definitions
        <type> <field_name>;
        // ...
    };
};
```

### Domain Configuration

Domain IDs are specified in the first line of each IDL file:
```idl
//domain=1
```

This domain ID is:
- Used during code generation
- Injected into generated `*main.cxx` files
- Used for DDS domain participant creation
- Critical for DDS topic routing

### Generated Structure

For each IDL file (e.g., `CoreData.idl`), the generator creates:

```
<Module>_idl_generated/
├── <Module>.hpp                    # Main type header
├── <Module>.cxx                    # Type implementation
├── <Module>PubSubTypes.hpp         # DDS PubSubTypes header
├── <Module>PubSubTypes.cxx         # PubSubTypes implementation
├── <Module>PublisherApp.hpp        # Publisher application header
├── <Module>PublisherApp.cxx       # Publisher application source
├── <Module>SubscriberApp.hpp       # Subscriber application header
├── <Module>SubscriberApp.cxx      # Subscriber application source
├── <Module>main.cxx                # Main entry point
├── CMakeLists.txt                  # Build configuration
└── build/                          # Build output directory
    ├── lib<Module>_lib.a          # Static library
    └── <Module>main               # Executable
```

## How It Works

### 1. IDL File Definition

IDL files define data structures using OMG IDL syntax:

**Example: CoreData.idl**
```idl
//domain=1
module CoreData {
    struct FlatCoreData {
        double latitude;
        double longitude;
        float altitude;
        long time_seconds;
        unsigned long time_nano_seconds;
        float speed_mps;
        short orientation_degrees;
    };
};
```

**Key Features:**
- Module scoping for namespace organization
- Struct definitions for data structures
- Standard IDL types (double, float, long, etc.)
- Domain ID specification in comments

### 2. Code Generation Process

#### Step 1: IDL Generation (`generate_idl_code.sh`)

The generation process:

1. **Scans IDL Directory**: Finds all `*.idl` files in `IDL/` directory
2. **Validates Files**: Checks for syntax errors and domain IDs
3. **Runs fastddsgen**: Executes Fast-DDS generator for each IDL file
4. **Creates Output Directories**: Creates `*_idl_generated/` directories
5. **Generates Code**: Produces C++ headers, sources, and CMake files

**Command Execution:**
```bash
fastddsgen -replace -d <output_dir> <idl_file>
```

**Generated Components:**
- Type definitions (`<Module>.hpp/cxx`)
- PubSubTypes for DDS (`<Module>PubSubTypes.hpp/cxx`)
- Publisher/Subscriber applications
- CMake build configuration
- Main entry point (`<Module>main.cxx`)

#### Step 2: Domain ID Injection

After generation, domain IDs are injected into `*main.cxx` files:

```cpp
int domain_id = 1;  // From //domain=1 in IDL file
```

This ensures generated applications use the correct DDS domain.

#### Step 3: Code Patching

Generated code is enhanced with additional functionality:

1. **IDL Patcher** (`idl_default_data_patcher.py`):
   - Parses IDL files to understand structure
   - Generates default data assignments
   - Injects code into PublisherApp files

2. **JSON Patcher** (`json_reading_patcher.py`):
   - Replaces hardcoded data with JSON file reading
   - Enables scenario-based data injection
   - Must run after IDL patcher

3. **Security Patcher** (`apply_security_settings.py`):
   - Adds DDS security configuration
   - Configures authentication and encryption
   - Sets up certificate paths

### 3. Build Process

#### CMake Configuration

Each generated module includes a `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.10)
project(<Module>_idl_generated)

find_package(fastdds REQUIRED)
find_package(fastcdr REQUIRED)
find_package(OpenSSL REQUIRED)

add_executable(<Module>main <Module>main.cxx ...)
target_link_libraries(<Module>main fastdds fastcdr OpenSSL::SSL OpenSSL::Crypto)
```

#### Build Execution

```bash
cd <Module>_idl_generated
mkdir -p build
cd build
cmake ..
make
```

**Output:**
- Static library: `build/lib<Module>_lib.a`
- Executable: `build/<Module>main`

### 4. Generated Code Structure

#### Type Definition (`<Module>.hpp`)

```cpp
namespace CoreData {
    class FlatCoreData {
    public:
        double latitude() const;
        void latitude(double value);
        // ... other getters/setters
    private:
        double m_latitude;
        // ... other members
    };
}
```

#### PubSubTypes (`<Module>PubSubTypes.hpp`)

```cpp
class FlatCoreDataPubSubType : public eprosima::fastdds::dds::TopicDataType {
    // Serialization/deserialization
    // Type registration
    // Type support for DDS
};
```

#### Publisher Application (`<Module>PublisherApp.cxx`)

```cpp
class <Module>Publisher {
    DomainParticipant* participant;
    Publisher* publisher;
    DataWriter* writer;
    Topic* topic;
    
    void publish();
    void run();
};
```

#### Subscriber Application (`<Module>SubscriberApp.cxx`)

```cpp
class <Module>Subscriber {
    DomainParticipant* participant;
    Subscriber* subscriber;
    DataReader* reader;
    Topic* topic;
    
    void on_data_available(DataReader* reader);
    void run();
};
```

## Technologies Used

### Core Technologies

- **OMG IDL**: Industry-standard interface definition language
- **Fast-DDS Generator (fastddsgen)**: Java-based code generator
- **CMake**: Cross-platform build system
- **C++17**: Modern C++ standard for generated code
- **Fast-DDS**: DDS middleware implementation
- **Fast-CDR**: Serialization library

### Supporting Technologies

- **OpenSSL**: Cryptographic library (for security)
- **nlohmann/json**: JSON library (for scenario support)
- **Python**: Patching and automation scripts

## Requirements

### Build-Time Requirements

- **Java**: Version 8 or higher (for fastddsgen)
- **CMake**: Version 3.10 or higher
- **C++ Compiler**: GCC 7+, Clang 5+, or MSVC 2017+
- **Fast-DDS**: Installed and discoverable by CMake
- **Fast-CDR**: Installed and discoverable by CMake
- **OpenSSL**: Development libraries installed

### Runtime Requirements

- **Fast-DDS Runtime**: Shared libraries in library path
- **Fast-CDR Runtime**: Shared libraries in library path
- **OpenSSL Runtime**: Shared libraries in library path
- **Generated Libraries**: Static libraries from build process

## Usage

### Complete Workflow

#### 1. Generate IDL Code

```bash
cd scripts/sh
bash generate_idl_code.sh
```

This script:
- Checks for Java and fastddsgen
- Downloads JSON library if missing
- Finds OpenSSL paths dynamically
- Generates code for all IDL files

#### 2. Update Domain IDs

```bash
bash update_domain_ids.sh
```

Updates domain IDs in generated `*main.cxx` files based on IDL file comments.

#### 3. Apply Patches

**IDL Patcher** (generates default data):
```bash
python3 scripts/py/idl_default_data_patcher.py
```

**JSON Patcher** (adds JSON reading):
```bash
python3 scripts/py/json_reading_patcher.py
```

**Security Patcher** (adds security config):
```bash
python3 scripts/py/apply_security_settings.py
```

#### 4. Build Modules

```bash
bash build_idl_modules.sh
```

Or manually:
```bash
cd IDL/<Module>_idl_generated
mkdir -p build && cd build
cmake ..
make
```

### Individual Module Operations

#### Generate Single Module

```bash
cd IDL
fastddsgen -replace -d CoreData_idl_generated CoreData.idl
```

#### Build Single Module

```bash
cd IDL/CoreData_idl_generated
mkdir -p build && cd build
cmake ..
make
```

#### Run Publisher

```bash
cd IDL/CoreData_idl_generated/build
./CoreDatamain publisher
```

#### Run Subscriber

```bash
cd IDL/CoreData_idl_generated/build
./CoreDatamain subscriber
```

## IDL Modules in Project

### CoreData Module

**Purpose**: Basic aircraft position and status data

**Domain**: 1

**Structure**: `FlatCoreData`
- Position: latitude, longitude, altitude
- Time: seconds, nanoseconds
- Motion: speed_mps, orientation_degrees

**Variants**: CoreData2, CoreData3, CoreData4 (different domains)

### Intelligence Module

**Purpose**: Intelligence and target detection data

**Domain**: Specified in IDL file

**Structure**: Complex nested structures
- Vehicle status (battery, signal, errors)
- Target detection (ID, type, location, confidence)
- Task assignment (command, location, parameters)

### Messaging Module

**Purpose**: Status reports and command messaging

**Domain**: Specified in IDL file

**Structure**: Multi-part messaging
- Status reports (sender, location, status)
- Target detection information
- Task command assignments

## Code Patching System

### Patch Execution Order

**Critical**: Patches must be applied in this order:

1. **IDL Generation** (`generate_idl_code.sh`)
   - Creates base code structure
   - Generates PublisherApp/SubscriberApp files

2. **IDL Patcher** (`idl_default_data_patcher.py`)
   - Parses IDL files
   - Generates default data assignments
   - Injects AUTOGENERATED blocks

3. **JSON Patcher** (`json_reading_patcher.py`)
   - Replaces AUTOGENERATED blocks with JSON reading
   - Enables scenario-based data injection

4. **Security Patcher** (`apply_security_settings.py`)
   - Adds DDS security configuration
   - Configures certificate paths

5. **CMake Portability Fix** (`fix_cmake_rpath.py`)
   - Removes hardcoded paths
   - Adds RPATH settings

### Patch Markers

Patches use markers to identify injection points:

```cpp
// --- BEGIN AUTOGENERATED IDL PATCH (v9) ---
// Generated code here
// --- END AUTOGENERATED IDL PATCH (v9) ---
```

This allows:
- Idempotent patching (safe to run multiple times)
- Version tracking
- Easy identification of generated code

## Integration Points

### With Build System

- CMake integration for cross-platform builds
- Static library generation for linking
- Executable generation for testing

### With Security System

- Security patcher adds DDS security configuration
- Certificate paths are dynamically detected
- PC-specific certificate support

### With Scenario System

- JSON patcher enables scenario file reading
- Scenario files in `scenarios/` directory
- Data injection from JSON files

### With Monitoring System

- Generated libraries are linked into monitor
- Monitor subscribes to generated topics
- Type-safe data exchange

## Troubleshooting

### Generation Failures

**Problem**: fastddsgen fails or produces errors.

**Solutions**:
1. Check Java installation: `java -version`
2. Verify fastddsgen is in PATH: `which fastddsgen`
3. Check IDL syntax: Validate IDL file syntax
4. Review fastddsgen output for specific errors
5. Ensure output directory is writable

### Build Failures

**Problem**: CMake or make fails during build.

**Solutions**:
1. **Missing Dependencies**: Install Fast-DDS, Fast-CDR, OpenSSL
2. **CMake Path Issues**: Set `CMAKE_PREFIX_PATH` for Fast-DDS
3. **Compiler Issues**: Check C++17 support
4. **Library Paths**: Verify library paths in CMakeLists.txt
5. **Permissions**: Ensure write permissions on build directory

### Domain ID Mismatches

**Problem**: Publishers and subscribers don't communicate.

**Solutions**:
1. Verify domain IDs match in IDL files
2. Check `*main.cxx` files for correct domain_id
3. Ensure domain IDs are updated after generation
4. Verify DDS domain participant creation uses correct ID

### Type Mismatches

**Problem**: Type errors or serialization failures.

**Solutions**:
1. Ensure IDL files match across systems
2. Regenerate code if IDL files changed
3. Rebuild all modules after IDL changes
4. Check PubSubTypes match between publisher/subscriber

## Best Practices

### IDL Design

1. **Use Modules**: Organize types in modules for namespace management
2. **Consistent Naming**: Use consistent naming conventions
3. **Domain IDs**: Specify domain IDs clearly in comments
4. **Type Selection**: Choose appropriate IDL types for data
5. **Documentation**: Add comments explaining complex structures

### Code Generation

1. **Version Control**: Commit IDL files, not generated code
2. **Clean Generation**: Clean generated directories before regeneration
3. **Incremental Updates**: Only regenerate changed modules when possible
4. **Backup**: Keep backups before major IDL changes

### Build Management

1. **Parallel Builds**: Use `make -j` for faster builds
2. **Clean Builds**: Clean build directories for fresh builds
3. **Dependency Management**: Ensure all dependencies are installed
4. **Library Linking**: Verify static libraries are linked correctly

## Project Structure

See `IDL.mdd` for the complete project structure and operation diagrams.

## Notes

- IDL files are the single source of truth for data types
- Generated code should not be manually edited (use patchers instead)
- Domain IDs are critical for DDS topic routing
- All modules must be regenerated if IDL syntax changes
- The system supports incremental updates (regenerate only changed modules)
- Type safety is enforced at compile time through generated code
