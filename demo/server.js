const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// MODE: DDS-only (no JSON simulation, no local publishers)
const DDS_ONLY = !(process.env.DDS_ONLY === '0' || process.env.DDS_ONLY === 'false');

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Store active processes
let activeProcesses = [];

// Dynamic data structure for all IDL types
let dataStreams = {
  aircraft: {  // CoreData group - aircraft data
    coredata: [],
    coredata2: [],
    coredata3: [],
    coredata4: []
  },
  intelligence: [],
  messaging: []
};

// Available IDL types configuration
const IDL_TYPES = {
  aircraft: ['CoreData', 'CoreData2', 'CoreData3', 'CoreData4'],
  intelligence: ['Intelligence'],
  messaging: ['Messaging']
};

// Load scenario data dynamically
function loadScenarioData() {
  if (DDS_ONLY) {
    console.log('DDS_ONLY mode enabled: skipping scenario JSON load');
    return;
  }
  try {
    console.log('Loading scenario data for all IDL types...');
    
    // Load aircraft data (CoreData variants)
    IDL_TYPES.aircraft.forEach(type => {
      const filePath = path.join(__dirname, '..', 'scenarios', `${type}.json`);
      const streamKey = type.toLowerCase();
      
      console.log(`Attempting to load: ${filePath}`);
      
      if (fs.existsSync(filePath)) {
        dataStreams.aircraft[streamKey] = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        console.log(`✓ ${type} entries: ${dataStreams.aircraft[streamKey].length}`);
      } else {
        console.log(`✗ ${type}.json not found at ${filePath}, skipping...`);
        dataStreams.aircraft[streamKey] = [];
      }
    });

    // Load intelligence data
    IDL_TYPES.intelligence.forEach(type => {
      const filePath = path.join(__dirname, '..', 'scenarios', `${type}.json`);
      
      if (fs.existsSync(filePath)) {
        dataStreams.intelligence = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        console.log(`${type} entries: ${dataStreams.intelligence.length}`);
      } else {
        console.log(`${type}.json not found, skipping...`);
        dataStreams.intelligence = [];
      }
    });

    // Load messaging data
    IDL_TYPES.messaging.forEach(type => {
      const filePath = path.join(__dirname, '..', 'scenarios', `${type}.json`);
      
      if (fs.existsSync(filePath)) {
        dataStreams.messaging = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        console.log(`${type} entries: ${dataStreams.messaging.length}`);
      } else {
        console.log(`${type}.json not found, skipping...`);
        dataStreams.messaging = [];
      }
    });

    console.log('Scenario data loaded successfully');
    console.log(`Total aircraft data streams loaded: ${Object.keys(dataStreams.aircraft).length}`);
    console.log(`Intelligence entries: ${dataStreams.intelligence.length}`);
    console.log(`Messaging entries: ${dataStreams.messaging.length}`);
  } catch (error) {
    console.error('Error loading scenario data:', error);
  }
}

// Parse DDS subscriber stdout blocks of the form:
// TOPIC: <aircraft|intelligence|messaging>\nSample 'N' RECEIVED\n - {...}
function createDDSStdoutParser(procMeta) {
  let buffer = '';
  let currentGroup = procMeta.group || 'aircraft';
  let currentAircraftSubtype = 'coredata'; // coredata, coredata2, coredata3, coredata4

  function tryEmitParsedObjects() {
    // Handle topic switch lines
    let topicIdx;
    while ((topicIdx = buffer.indexOf('TOPIC: ')) !== -1) {
      const end = buffer.indexOf('\n', topicIdx);
      if (end === -1) break;
      const line = buffer.substring(topicIdx, end).trim();
      const after = line.split('TOPIC: ')[1]?.trim().toLowerCase();
      const parts = after ? after.split(/\s+/) : [];
      const tag = parts[0];
      if (tag === 'aircraft' || tag === 'intelligence' || tag === 'messaging') {
        currentGroup = tag;
        if (tag === 'aircraft') {
          // Optional subtype: coredata|coredata2|coredata3|coredata4
          currentAircraftSubtype = parts[1] || 'coredata';
        }
      }
      buffer = buffer.slice(end + 1);
    }

    // We expect a block starting with " - {" and ending with the first matching "}"
    while (true) {
      const startIdx = buffer.indexOf(' - {');
      if (startIdx === -1) break;
      // Find balanced closing '}' for this block
      let i = startIdx + 3;
      let depth = 0;
      let endIdx = -1;
      for (; i < buffer.length; i++) {
        const ch = buffer[i];
        if (ch === '{') depth++;
        else if (ch === '}') {
          depth--;
          if (depth === 0) { endIdx = i; break; }
        }
      }
      if (endIdx === -1) break; // wait for more data

      let content = buffer.substring(startIdx + 3, endIdx + 1);
      buffer = buffer.slice(endIdx + 1);

      try {
        // Strip interleaved monitor noise lines/snippets
        let normalized = content
          .replace(/^.*TOPIC:.*$/gm, '')
          .replace(/\[domain=[^\]]*\]/g, '');
        // 1) Quote keys
        normalized = normalized.replace(/([\{,\s])([a-zA-Z_][a-zA-Z0-9_]*)\s*:/g, '$1"$2":');
        // 2) Normalize quotes
        normalized = normalized.replace(/'/g, '"');
        // 3) Quote unquoted string values safely (until comma or closing brace)
        normalized = normalized.replace(/:\s*([^\s\",\}\{][^,\}]*)/g, (m, v) => {
          const raw = v.trim();
          if (/^(true|false|null)$/i.test(raw)) return `: ${raw.toLowerCase()}`;
          if (/^-?\d+(?:\.\d+)?$/.test(raw)) return `: ${raw}`; // number
          return `: "${raw}"`;
        });
        // 4) Remove trailing commas before closing brace
        normalized = normalized.replace(/,(?=\s*\})/g, '');
        const obj = JSON.parse(normalized);

        if (currentGroup === 'aircraft') {
          const subtype = currentAircraftSubtype || 'coredata';
          let aircraftId = 1;
          if (subtype === 'coredata2') aircraftId = 2;
          else if (subtype === 'coredata3') aircraftId = 3;
          else if (subtype === 'coredata4') aircraftId = 4;

          const payload = {
            ...obj,
            // UI fields
            id: aircraftId,
            speed_kmh: (obj.speed_mps || 0) * 3.6,
            heading: obj.orientation_degrees,
            timestamp: Date.now(),
            type: 'aircraft',
            aircraftType: subtype,
            callsign: `AIRCRAFT-${aircraftId}`,
            isOwnAircraft: aircraftId === 1,
            // Scenario-compatible aliases
            speed_mps: obj.speed_mps,
            orientation_degrees: obj.orientation_degrees,
            time_seconds: obj.time_seconds,
            time_nano_seconds: obj.time_nano_seconds
          };
          io.emit('aircraftData', payload);
        } else if (currentGroup === 'intelligence') {
          // Emit with both scenario-compatible keys and UI-friendly aliases
          const mapped = {
            ...obj,
            timestamp: Date.now(),
            type: 'target',
            // Map markers (UI)
            latitude: obj.td_location_latitude,
            longitude: obj.td_location_longitude,
            altitude: obj.td_location_altitude,
            // Scenario-compatible (already in obj):
            // vs_task_status, vs_battery_percentage, vs_signal_strength_dbm, vs_system_error,
            // td_target_ID, td_target_type, td_location_* , td_confidence_level, td_description,
            // td_raw_data_link, ta_command, ta_location_*
            // UI aliases for convenience
            vs_mission_status: obj.vs_task_status,
            vs_battery_level: obj.vs_battery_percentage,
            td_target_id: obj.td_target_ID
          };
          io.emit('intelligence', mapped);
        } else if (currentGroup === 'messaging') {
          // Map to scenario-compatible keys, plus keep UI-friendly fields
          const mapped = {
            ...obj,
            timestamp: Date.now(),
            type: 'message',
            // Primary map location: StatusReport location
            latitude: obj.sr_location_latitude,
            longitude: obj.sr_location_longitude,
            altitude: obj.sr_location_altitude,
            // Scenario-compatible (aliases from DDS fields)
            sr_sender_id: obj.sr_header_sender_id,
            sr_timestamp: obj.sr_header_time_seconds,
            sr_status: obj.sr_status_task_status,
            sr_battery_level: obj.sr_status_battery_percentage,
            // sr_fuel_level is not present in DDS stream; leave undefined if missing
            sr_system_health: typeof obj.sr_status_system_error === 'boolean' ? !obj.sr_status_system_error : obj.sr_status_system_error,
            // Detection
            cd_target_ID: obj.cd_detection_target_ID,
            cd_target_type: obj.cd_detection_target_type,
            cd_detection_latitude: obj.cd_detection_loc_latitude,
            cd_detection_longitude: obj.cd_detection_loc_longitude,
            cd_detection_altitude: obj.cd_detection_loc_altitude,
            cd_detection_time_seconds: obj.cd_detection_loc_time_seconds,
            cd_detection_time_nano_seconds: obj.cd_detection_loc_time_nano_seconds,
            cd_detection_speed_mps: obj.cd_detection_loc_speed_mps,
            cd_detection_orientation_degrees: obj.cd_detection_loc_orientation_degrees,
            cd_confidence_level: obj.cd_detection_confidence_level,
            cd_description: obj.cd_detection_description,
            cd_raw_data_link: obj.cd_detection_raw_data_link,
            // Task Command
            tc_receiver_id: obj.tc_receiver_id,
            tc_assignment_command: obj.tc_assignment_command,
            tc_assignment_location_latitude: obj.tc_assignment_loc_latitude,
            tc_assignment_location_longitude: obj.tc_assignment_loc_longitude,
            tc_assignment_location_altitude: obj.tc_assignment_loc_altitude,
            tc_assignment_location_time_seconds: obj.tc_assignment_loc_time_seconds,
            tc_assignment_location_time_nano_seconds: obj.tc_assignment_loc_time_nano_seconds,
            tc_assignment_location_speed_mps: obj.tc_assignment_loc_speed_mps,
            tc_assignment_location_orientation_degrees: obj.tc_assignment_loc_orientation_degrees,
            // Keep UI-friendly aliases too
            sr_sender_id_alias: obj.sr_header_sender_id,
            cd_target_id: obj.cd_detection_target_ID,
            cd_target_type_alias: obj.cd_detection_target_type
          };
          io.emit('messaging', mapped);
        }
      } catch (e) {
        console.error(`${procMeta.name} parse error:`, e.message);
      }
    }
  }

  return (data) => {
    buffer += data.toString();
    tryEmitParsedObjects();
  };
}

// Start standalone monitoring process (aggregated)
function startMonitorProcess() {
  const srcPath = path.join(__dirname, '..', 'monitoring', 'monitor');
  const buildPath = path.join(__dirname, '..', 'monitoring', 'build', 'monitor');
  const monitorPath = fs.existsSync(srcPath) ? srcPath : buildPath;
  if (fs.existsSync(monitorPath)) {
    console.log('Starting unified monitor subscriber...');
    // Pass MONITOR_DOMAINS to monitor as CLI arg if present
    const monitorArgs = [];
    if (process.env.MONITOR_DOMAINS && String(process.env.MONITOR_DOMAINS).trim().length > 0) {
      monitorArgs.push(String(process.env.MONITOR_DOMAINS).trim());
    }
    const childProcess = spawn(monitorPath, monitorArgs, { cwd: path.dirname(monitorPath) });

    const stdoutHandler = createDDSStdoutParser({ name: 'Monitor', group: 'aircraft' });
    childProcess.stdout.on('data', (data) => {
      console.log(`Monitor: ${data}`);
      if (DDS_ONLY) {
        stdoutHandler(data);
      }
    });

    childProcess.stderr.on('data', (data) => {
      console.error(`Monitor Error: ${data}`);
    });

    activeProcesses.push({ name: 'Monitor', process: childProcess, group: 'aircraft' });
  } else {
    console.log(`Monitor executable not found at: ${srcPath} or ${buildPath}`);
  }
}

// Start only the unified monitor process
function startDDSProcesses() {
  if (DDS_ONLY) {
    // Only start the unified monitor - no individual subscribers
    startMonitorProcess();
  } else {
    console.log('DDS_ONLY mode disabled: starting individual subscribers');
    const processes = [
      // Aircraft subscribers (CoreData variants)
      { name: 'CoreData', path: '../IDL/CoreData_idl_generated/CoreDatamain', group: 'aircraft' },
      { name: 'CoreData2', path: '../IDL/CoreData2_idl_generated/CoreData2main', group: 'aircraft' },
      { name: 'CoreData3', path: '../IDL/CoreData3_idl_generated/CoreData3main', group: 'aircraft' },
      { name: 'CoreData4', path: '../IDL/CoreData4_idl_generated/CoreData4main', group: 'aircraft' },
      // Other subscribers
      { name: 'Intelligence', path: '../IDL/Intelligence_idl_generated/Intelligencemain', group: 'intelligence' },
      { name: 'Messaging', path: '../IDL/Messaging_idl_generated/Messagingmain', group: 'messaging' }
    ];

    processes.forEach(proc => {
      // Cross-platform executable path handling
      const executablePath = process.platform === 'win32' ? `${proc.path}.exe` : proc.path;
      const fullPath = path.join(__dirname, executablePath);
      
      if (fs.existsSync(fullPath)) {
        console.log(`Starting ${proc.name} subscriber...`);
        const childProcess = spawn(fullPath, ['subscriber'], { cwd: path.dirname(fullPath) });
        
        const stdoutHandler = createDDSStdoutParser(proc);
        childProcess.stdout.on('data', (data) => {
          console.log(`${proc.name}: ${data}`);
          stdoutHandler(data);
        });

        childProcess.stderr.on('data', (data) => {
          console.error(`${proc.name} Error: ${data}`);
        });

        activeProcesses.push({ name: proc.name, process: childProcess, group: proc.group });
      } else {
        console.log(`${proc.name} subscriber executable not found: ${fullPath}`);
      }
    });
  }
}

// Start DDS publisher processes for all IDL types
function startDDSPublishers() {
  if (DDS_ONLY) {
    console.log('DDS_ONLY mode enabled: skipping local DDS publishers');
    return;
  }
  const publishers = [
    // Aircraft publishers (CoreData variants)
    { name: 'CoreDataPub', path: '../IDL/CoreData_idl_generated/CoreDatamain', group: 'aircraft' },
    { name: 'CoreData2Pub', path: '../IDL/CoreData2_idl_generated/CoreData2main', group: 'aircraft' },
    { name: 'CoreData3Pub', path: '../IDL/CoreData3_idl_generated/CoreData3main', group: 'aircraft' },
    { name: 'CoreData4Pub', path: '../IDL/CoreData4_idl_generated/CoreData4main', group: 'aircraft' },
    // Other publishers
    { name: 'IntelligencePub', path: '../IDL/Intelligence_idl_generated/Intelligencemain', group: 'intelligence' },
    { name: 'MessagingPub', path: '../IDL/Messaging_idl_generated/Messagingmain', group: 'messaging' }
  ];

  publishers.forEach(pub => {
    // Cross-platform executable path handling
    const executablePath = process.platform === 'win32' ? `${pub.path}.exe` : pub.path;
    const fullPath = path.join(__dirname, executablePath);
    
    if (fs.existsSync(fullPath)) {
      console.log(`Starting ${pub.name}...`);
      const childProcess = spawn(fullPath, ['publisher'], { cwd: path.dirname(fullPath) });
      
      childProcess.stdout.on('data', (data) => {
        console.log(`${pub.name}: ${data}`);
      });

      childProcess.stderr.on('data', (data) => {
        console.error(`${pub.name} Error: ${data}`);
      });

      activeProcesses.push({ name: pub.name, process: childProcess, group: pub.group });
    } else {
      console.log(`${pub.name} executable not found: ${fullPath}`);
    }
  });
}

// Simulate real-time data streaming for all IDL types
let dataIndex = { 
  aircraft: { coredata: 0, coredata2: 0, coredata3: 0, coredata4: 0 },
  intelligence: 0, 
  messaging: 0 
};

function simulateDataStream() {
  if (DDS_ONLY) {
    console.log('DDS_ONLY mode enabled: skipping JSON-based simulation');
    return;
  }
  console.log('Starting data stream simulation...');
  
  setInterval(() => {
    // Emit all aircraft data (CoreData variants)
    Object.keys(dataStreams.aircraft).forEach(aircraftType => {
      const aircraftData = dataStreams.aircraft[aircraftType];
      if (aircraftData.length > 0) {
        const data = aircraftData[dataIndex.aircraft[aircraftType] % aircraftData.length];
        
        // Determine aircraft ID based on type
        let aircraftId = 1;
        if (aircraftType === 'coredata2') aircraftId = 2;
        else if (aircraftType === 'coredata3') aircraftId = 3;
        else if (aircraftType === 'coredata4') aircraftId = 4;
        
        const aircraftPayload = {
          ...data,
          // Add frontend-compatible field names
          id: aircraftId,
          speed_kmh: data.speed_mps * 3.6, // Convert m/s to km/h
          heading: data.orientation_degrees,
          timestamp: Date.now(),
          type: 'aircraft',
          aircraftType: aircraftType,
          callsign: `UÇAK-${aircraftId}`,
          isOwnAircraft: aircraftId === 1 // First aircraft is own aircraft
        };
        
        console.log(`Emitting aircraftData for ${aircraftType} (ID: ${aircraftId})`);
        io.emit('aircraftData', aircraftPayload);
        
        dataIndex.aircraft[aircraftType]++;
      } else {
        console.log(`No data available for ${aircraftType}`);
      }
    });

    // Emit Intelligence data (targets)
    if (dataStreams.intelligence.length > 0) {
      const intData = dataStreams.intelligence[dataIndex.intelligence % dataStreams.intelligence.length];
      io.emit('intelligence', {
        ...intData,
        // Add frontend-compatible field names
        vs_mission_status: getTaskStatusText(intData.vs_task_status),
        vs_battery_level: intData.vs_battery_percentage,
        td_target_id: intData.td_target_ID,
        // Add location data for map markers
        latitude: intData.td_location_latitude,
        longitude: intData.td_location_longitude,
        altitude: intData.td_location_altitude,
        timestamp: Date.now(),
        type: 'target'
      });
      dataIndex.intelligence++;
    }

    // Emit Messaging data
    if (dataStreams.messaging.length > 0) {
      const msgData = dataStreams.messaging[dataIndex.messaging % dataStreams.messaging.length];
      io.emit('messaging', {
        ...msgData,
        // Add frontend-compatible field names
        sr_sender_id: msgData.sr_sender_id,
        cd_target_id: msgData.cd_target_ID,
        tc_command: msgData.tc_assignment_command,
        // Add location data for map markers
        latitude: msgData.sr_location_latitude,
        longitude: msgData.sr_location_longitude,
        altitude: msgData.sr_location_altitude,
        timestamp: Date.now(),
        type: 'message'
      });
      dataIndex.messaging++;
    }
  }, 1000); // Update every 1 second for more dynamic display
}

// Helper function to convert task status numbers to text
function getTaskStatusText(status) {
  const statusMap = {
    1: 'PATROL',
    2: 'INTERCEPT', 
    3: 'SURVEILLANCE',
    4: 'RECONNAISSANCE',
    5: 'STANDBY'
  };
  return statusMap[status] || 'UNKNOWN';
}

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // Send initial data
  socket.emit('systemStatus', {
    status: 'operational',
    activeProcesses: activeProcesses.map(p => p.name),
    dataStreams: {
      aircraft: Object.keys(dataStreams.aircraft).length,
      intelligence: dataStreams.intelligence.length,
      messaging: dataStreams.messaging.length
    },
    mode: DDS_ONLY ? 'DDS_ONLY' : 'SIMULATION+DDS'
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });

  socket.on('requestData', (type) => {
    if (DDS_ONLY) {
      // No backfill in DDS-only mode
      return;
    }
    switch(type) {
      case 'coreData':
        if (dataStreams.coreData.length > 0) {
          socket.emit('coreData', dataStreams.coreData[0]);
        }
        break;
      case 'intelligence':
        if (dataStreams.intelligence.length > 0) {
          socket.emit('intelligence', dataStreams.intelligence[0]);
        }
        break;
      case 'messaging':
        if (dataStreams.messaging.length > 0) {
          socket.emit('messaging', dataStreams.messaging[0]);
        }
        break;
    }
  });
});

// Cleanup function
function cleanup() {
  console.log('Shutting down server and processes...');
  activeProcesses.forEach(proc => {
    try {
      proc.process.kill();
      console.log(`Terminated ${proc.name}`);
    } catch (error) {
      console.error(`Error terminating ${proc.name}:`, error);
    }
  });
  process.exit(0);
}

// Handle shutdown signals - only for manual termination
process.on('SIGINT', () => {
  console.log('Received SIGINT, shutting down gracefully...');
  cleanup();
});

process.on('SIGTERM', () => {
  console.log('Received SIGTERM, shutting down gracefully...');
  cleanup();
});

// Remove the automatic exit handler that was causing premature shutdowns
// process.on('exit', cleanup);

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/api/status', (req, res) => {
  res.json({
    status: 'operational',
    activeProcesses: activeProcesses.map(p => p.name),
    dataStreams: {
      aircraft: Object.keys(dataStreams.aircraft).length,
      intelligence: dataStreams.intelligence.length,
      messaging: dataStreams.messaging.length
    },
    mode: DDS_ONLY ? 'DDS_ONLY' : 'SIMULATION+DDS'
  });
});

// Initialize and start server
const PORT = process.env.PORT || 3000;

console.log('Initializing Military DDS Dashboard...');
loadScenarioData();

server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Dashboard available at: http://localhost:${PORT}`);
  
  // Auto-start monitor in DDS_ONLY mode so stdout is parsed and forwarded to clients
  if (DDS_ONLY) {
    startMonitorProcess();
  } else {
    // If not DDS_ONLY, you can optionally load scenarios and simulate
    loadScenarioData();
  }
});