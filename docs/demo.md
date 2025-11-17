# Demo Dashboard System

## Overview

The Demo Dashboard System is a comprehensive web-based real-time visualization platform for DDS (Data Distribution Service) data streams. It provides a professional military command and control interface with interactive geospatial visualization, real-time data streaming, and multi-domain DDS integration.

## Purpose

The demo dashboard serves as the primary visualization and monitoring interface for the DDS project, enabling:

- **Real-Time Data Visualization**: Display DDS data streams in real-time with sub-second latency
- **Geospatial Intelligence**: Interactive map-based visualization of aircraft positions, targets, and mission data
- **Multi-Domain Monitoring**: Simultaneous monitoring of multiple DDS domains (0-5) and topics
- **Command & Control Interface**: Professional military-style interface for operational scenarios
- **Data Integration**: Seamless integration with DDS publishers, subscribers, and monitoring systems

## Architecture

### System Components

#### Backend (Node.js Server)

1. **server.js** - Express.js HTTP server with Socket.IO WebSocket support
   - Handles HTTP requests and serves static files
   - Manages WebSocket connections for real-time data streaming
   - Parses DDS stdout output from monitoring processes
   - Manages DDS process lifecycle (start/stop/monitor)

2. **Process Management**
   - Unified monitor process integration
   - Individual subscriber process management
   - Publisher process tracking (optional)
   - Process health monitoring and restart capabilities

#### Frontend (Web Application)

1. **public/index.html** - Main HTML structure
   - Semantic HTML5 structure
   - Responsive layout design
   - Integration points for map and data panels

2. **public/app.js** - Frontend application logic
   - WebSocket client implementation
   - Leaflet.js map integration and management
   - Real-time data processing and visualization
   - UI state management and event handling

3. **public/style.css** - Styling and theming
   - Military command control aesthetic
   - Responsive design for various screen sizes
   - Professional color scheme and typography

#### Launch Infrastructure

1. **demo.sh** - Linux launch script
   - Dependency checking (Node.js, npm)
   - Automatic dependency installation
   - Process initialization and tracking
   - User guidance for publisher startup

2. **package.json** - Node.js project configuration
   - Dependency declarations
   - Script definitions
   - Project metadata

## How It Works

### 1. Server Initialization

Upon startup, the server:

1. **Creates Express Application**
   - Configures middleware (CORS, JSON parsing, static file serving)
   - Sets up route handlers
   - Initializes Socket.IO with CORS support

2. **Loads Configuration**
   - Determines DDS_ONLY mode (default: enabled)
   - Reads environment variables (PORT, MONITOR_DOMAINS)
   - Configures data stream structures

3. **Initializes Data Structures**
   - Sets up data streams for aircraft (CoreData variants)
   - Initializes intelligence and messaging streams
   - Prepares WebSocket event handlers

### 2. DDS Integration Modes

#### DDS_ONLY Mode (Default - Production)

**Characteristics:**
- Connects only to real DDS data streams
- No JSON simulation or mock data
- Starts unified monitor process automatically
- Parses actual DDS stdout output
- Full security integration

**Workflow:**
1. Server starts unified monitor (`monitoring/build/monitor`)
2. Monitor subscribes to DDS topics across specified domains
3. Monitor prints received samples to stdout
4. Server parses stdout using regex patterns
5. Parsed data is emitted via WebSocket to connected clients

#### Simulation Mode (DDS_ONLY=false)

**Characteristics:**
- Can load JSON scenario files for testing
- Starts individual subscriber processes
- Supports data simulation from JSON files
- Useful for development and testing without DDS infrastructure

**Workflow:**
1. Server loads JSON scenario files from `scenarios/` directory
2. Starts individual subscriber processes per module
3. Processes can use simulated or real data
4. Data flows through same WebSocket pipeline

### 3. Data Flow Architecture

```
┌─────────────────┐
│ DDS Publishers │  (CoreData, Intelligence, Messaging)
└────────┬────────┘
         │ DDS Topics (RTPS)
         │
         ▼
┌─────────────────┐
│ Unified Monitor │  (monitoring/build/monitor)
│  or Individual  │  Subscribes to multiple domains/topics
│  Subscribers    │
└────────┬────────┘
         │ stdout (formatted text)
         │
         ▼
┌─────────────────┐
│  server.js      │  Parses stdout with regex
│  (Parser)       │  Extracts domain, topic, data fields
└────────┬────────┘
         │ WebSocket Events
         │ (aircraftData, intelligence, messaging)
         │
         ▼
┌─────────────────┐
│  Frontend       │  Receives events via Socket.IO
│  (app.js)       │  Updates map markers and data panels
└─────────────────┘
```

### 4. Data Parsing Mechanism

The server uses sophisticated regex-based parsing to extract structured data from monitor stdout:

**Pattern Recognition:**
- Domain identification: `[domain=X]`
- Topic identification: `TOPIC: aircraft <subtype>`
- Sample extraction: JSON-like data structures
- Field mapping: Maps DDS field names to UI-friendly aliases

**Data Transformation:**
- Converts DDS field names to scenario-compatible keys
- Adds UI-friendly aliases (e.g., `latitude`, `longitude` for map)
- Adds timestamps and metadata
- Groups data by type (aircraft, intelligence, messaging)

### 5. WebSocket Communication

**Server → Client Events:**
- `aircraftData` - Aircraft position and status updates
- `intelligence` - Intelligence target detections
- `messaging` - Status reports and task commands
- `systemStatus` - System health and connection status

**Client → Server Events:**
- `connect` - Client connection established
- `disconnect` - Client disconnection
- Custom events for user interactions (if implemented)

### 6. Frontend Map Visualization

**Map Features:**
- **Leaflet.js Integration**: Industry-standard mapping library
- **Multiple Map Types**: Satellite imagery and street maps
- **Dynamic Markers**: Aircraft, targets, messages with custom icons
- **Real-Time Updates**: Markers move and update in real-time
- **Auto-Follow**: Option to follow selected aircraft
- **Zoom/Pan Controls**: Standard map navigation

**Data Panels:**
- **Aircraft Panel**: Selected aircraft details (position, speed, altitude, orientation)
- **Intelligence Panel**: Target detection information
- **Messaging Panel**: Status reports and task commands
- **System Status**: Connection status and system health indicators

## Technologies Used

### Backend
- **Node.js** (v14+ recommended) - JavaScript runtime
- **Express.js** (^4.18.2) - Web application framework
- **Socket.IO** (^4.7.2) - WebSocket library for real-time communication
- **CORS** (^2.8.5) - Cross-origin resource sharing middleware

### Frontend
- **Vanilla JavaScript** - No framework dependencies
- **Leaflet.js** (1.9.4) - Interactive map library
- **Font Awesome** (6.5.1) - Icon library
- **HTML5/CSS3** - Modern web standards

### Integration
- **DDS (Fast-DDS)** - Data distribution middleware
- **Process Management** - Child process spawning and monitoring
- **Regex Parsing** - Text-based data extraction

## Requirements

### System Requirements

- **Operating System**: Linux (Ubuntu/Debian recommended), Windows (with WSL)
- **Node.js**: Version 14.0 or higher
- **npm**: Version 6.0 or higher (comes with Node.js)
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Network**: Internet connection for map tiles (Leaflet)

### DDS Requirements

- **Fast-DDS**: Installed and configured
- **DDS Publishers**: Built and executable (IDL modules)
- **DDS Monitor**: Built (`monitoring/build/monitor`)
- **Certificates**: Valid DDS security certificates (if using security)

### Browser Requirements

- **Modern Browser**: Chrome 90+, Firefox 88+, Edge 90+, Safari 14+
- **WebSocket Support**: Required (all modern browsers)
- **JavaScript Enabled**: Required
- **Internet Connection**: For Leaflet map tiles

## Usage

### Initial Setup

#### 1. Install Dependencies

```bash
cd demo
npm install
```

This installs all required Node.js packages listed in `package.json`.

#### 2. Verify DDS Components

Ensure DDS components are built:
```bash
# Build IDL modules
bash scripts/sh/IDL_BUILDER.sh

# Build monitor
bash monitoring/build.sh
```

### Running the Dashboard

#### Method 1: Using Launch Script (Recommended)

```bash
cd demo
bash demo.sh
```

The script will:
1. Check Node.js availability
2. Install dependencies if needed
3. Start the backend server
4. Display instructions for starting publishers

#### Method 2: Direct Node.js Execution

```bash
cd demo
node server.js
```

#### Method 3: Using npm Scripts

```bash
cd demo
npm start
```

### Configuration

#### Server Port

Default port: **3000**

Change via environment variable:
```bash
PORT=8080 node server.js
```

Or modify `server.js`:
```javascript
const PORT = process.env.PORT || 3000;
```

#### DDS_ONLY Mode

Control real DDS vs simulation:
```bash
# Real DDS only (default)
DDS_ONLY=1 node server.js

# Enable simulation mode
DDS_ONLY=0 node server.js
```

#### Monitor Domains

Specify which DDS domains to monitor:
```bash
MONITOR_DOMAINS="0,1,2" node server.js
```

Supports comma-separated or range syntax:
```bash
MONITOR_DOMAINS="0-3,5" node server.js
```

### Accessing the Dashboard

1. **Start the server** (see above)
2. **Open web browser**
3. **Navigate to**: `http://localhost:3000` (or configured port)
4. **Dashboard loads automatically**

### Starting DDS Publishers

After starting the demo server, start DDS publishers in separate terminals:

```bash
# CoreData Publisher (Domain 1)
cd IDL/CoreData_idl_generated/build
./CoreDatamain publisher

# CoreData2 Publisher (Domain 2)
cd IDL/CoreData2_idl_generated/build
./CoreData2main publisher

# Intelligence Publisher
cd IDL/Intelligence_idl_generated/build
./Intelligencemain publisher

# Messaging Publisher
cd IDL/Messaging_idl_generated/build
./Messagingmain publisher
```

Or use the unified monitor (recommended):
```bash
cd monitoring
bash monitor.sh
```

The monitor subscribes to all topics across specified domains.

## Data Format

### Aircraft Data (CoreData)

```javascript
{
  domain: 1,
  type: 'aircraft',
  subtype: 'coredata',  // or 'coredata2', 'coredata3', 'coredata4'
  latitude: 39.9334,
  longitude: 32.8597,
  altitude: 1500.0,
  speed_mps: 250.5,
  orientation_degrees: 45.0,
  time_seconds: 1730352000,
  time_nano_seconds: 500000000,
  timestamp: 1730352000500  // Added by server
}
```

### Intelligence Data

```javascript
{
  type: 'target',
  td_target_ID: 'TGT001',
  td_target_type: 1,
  td_location_latitude: 40.1234,
  td_location_longitude: 33.5678,
  td_location_altitude: 1200.0,
  td_confidence_level: 0.95,
  td_description: 'Hostile target detected',
  timestamp: Date.now()
}
```

### Messaging Data

```javascript
{
  type: 'message',
  sr_header_sender_id: 'UAV01',
  sr_status_task_status: 'PATROL',
  sr_status_battery_percentage: 85.5,
  cd_detection_target_ID: 'TGT001',
  tc_assignment_command: 'ENGAGE',
  timestamp: Date.now()
}
```

## Integration Points

### With Monitoring System

The demo server can automatically start the unified monitor:
- Detects monitor executable at `monitoring/monitor` or `monitoring/build/monitor`
- Passes `MONITOR_DOMAINS` environment variable if set
- Parses monitor stdout output
- Forwards parsed data to dashboard via WebSocket

### With DDS Security

The dashboard works seamlessly with DDS security:
- Monitor uses PKI-DH authentication and AES-GCM-GMAC encryption
- Publishers must have matching certificates
- Certificate paths are dynamically detected
- Security is transparent to the dashboard (handled at DDS layer)

### With Scenario Files

When `DDS_ONLY=false`, the server can:
- Load JSON scenario files from `scenarios/` directory
- Use scenario data for simulation
- Support testing without active DDS infrastructure

## Troubleshooting

### Server Won't Start

**Problem**: Server fails to start or crashes immediately.

**Solutions**:
1. Check Node.js installation: `node --version` (should be 14+)
2. Verify dependencies: `npm install` in `demo/` directory
3. Check port availability: `lsof -i :3000` (Linux) or `netstat -ano | findstr :3000` (Windows)
4. Review server logs for error messages
5. Check file permissions on `server.js` and `public/` directory

### No Data on Dashboard

**Problem**: Dashboard loads but shows no data.

**Solutions**:
1. **Verify DDS Publishers**: Ensure publishers are running and sending data
2. **Check Monitor**: Monitor should be receiving data (check stdout)
3. **Verify WebSocket Connection**: Check browser console for connection errors
4. **Check Domain IDs**: Publishers and monitor must use matching domain IDs
5. **Verify Security**: If using security, ensure certificates are valid
6. **Check Network**: DDS uses UDP multicast (check firewall settings)

### Map Not Loading

**Problem**: Map tiles don't load or map is blank.

**Solutions**:
1. **Check Internet Connection**: Leaflet requires internet for map tiles
2. **Browser Console**: Check for JavaScript errors or network failures
3. **CDN Access**: Verify access to Leaflet CDN (may be blocked by firewall)
4. **Browser Compatibility**: Ensure browser supports Leaflet.js
5. **Clear Browser Cache**: Try clearing cache and reloading

### WebSocket Connection Issues

**Problem**: WebSocket connection fails or disconnects frequently.

**Solutions**:
1. **Check Server Status**: Verify server is running and accessible
2. **Firewall Settings**: Ensure port 3000 (or configured port) is open
3. **Proxy Settings**: If behind proxy, configure Socket.IO accordingly
4. **Browser Compatibility**: Ensure browser supports WebSocket
5. **Network Issues**: Check for network connectivity problems

### Process Management Issues

**Problem**: DDS processes not starting or crashing.

**Solutions**:
1. **Check PID File**: Review `demo/processes.pid` for process tracking
2. **Kill Stale Processes**: `pkill -f "node server.js"` or `pkill -f monitor`
3. **Verify Executables**: Ensure DDS executables are built and executable
4. **Check Permissions**: Verify execute permissions on scripts and binaries
5. **Review Logs**: Check stdout/stderr for error messages

## Best Practices

### Development

1. **Use DDS_ONLY Mode**: Always test with real DDS data when possible
2. **Monitor Logs**: Keep server logs visible during development
3. **Browser DevTools**: Use browser developer tools for debugging
4. **Incremental Testing**: Test components individually before integration

### Production

1. **Security**: Always use DDS security in production environments
2. **Error Handling**: Implement comprehensive error handling
3. **Monitoring**: Set up process monitoring and health checks
4. **Logging**: Implement proper logging for troubleshooting
5. **Performance**: Monitor WebSocket connection count and data throughput

### Deployment

1. **Environment Variables**: Use environment variables for configuration
2. **Process Management**: Use process managers (PM2, systemd) for production
3. **Reverse Proxy**: Use nginx or Apache as reverse proxy
4. **SSL/TLS**: Enable HTTPS for production deployments
5. **Resource Limits**: Set appropriate memory and CPU limits

## Project Structure

```
demo/
├── server.js              # Backend server (Express + Socket.IO)
├── demo.sh                # Linux launch script
├── package.json           # Node.js dependencies and scripts
├── processes.pid          # Process tracking file (auto-generated)
└── public/                # Frontend files
    ├── index.html         # Main HTML structure
    ├── app.js             # Frontend JavaScript logic
    └── style.css          # Styling and theming
```

## Operation Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DDS Infrastructure                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │Publisher │  │Publisher │  │Publisher │                  │
│  │CoreData  │  │Intelligence│ │Messaging │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       │             │             │                         │
│       └─────────────┴─────────────┘                         │
│                    │ DDS Topics                             │
│                    ▼                                         │
│         ┌──────────────────────┐                            │
│         │  Unified Monitor     │                            │
│         │  (monitoring/monitor)│                            │
│         └──────────┬───────────┘                            │
└────────────────────┼────────────────────────────────────────┘
                     │ stdout (parsed)
                     ▼
         ┌──────────────────────┐
         │   Demo Server        │
         │   (server.js)        │
         │   - Parse stdout     │
         │   - WebSocket emit   │
         └──────────┬───────────┘
                    │ WebSocket Events
                    ▼
         ┌──────────────────────┐
         │   Web Browser        │
         │   (Frontend)         │
         │   - Map visualization│
         │   - Data panels     │
         │   - Real-time updates│
         └──────────────────────┘
```

## Notes

- The dashboard is designed for real-time military command control scenarios
- Multiple browser tabs can connect simultaneously (each gets real-time updates)
- Process management is optional (publishers can be started manually)
- The system is designed to be portable and work across different environments
- Security is handled at the DDS layer, not in the dashboard itself
- The dashboard provides visualization only; it does not control DDS behavior
