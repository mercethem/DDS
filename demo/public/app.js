// Military Dashboard Application
class MilitaryDashboard {
    constructor() {
        this.socket = null;
        this.map = null;
        this.markers = new Map();
        this.currentMapMode = 'satellite';
        this.isDayMode = true;
        this.lastAircraftPosition = null; // Store last aircraft position
        this.targets = new Map();
        this.aircraftData = new Map(); // Store all aircraft data
        this.currentAircraftTab = 1; // Active aircraft tab
        
        // DDS traffic monitoring
        this.lastMessageAt = 0;
        this.trafficBannerEl = null;
        this.trafficTimer = null;
        
        this.init();
    }

    init() {
        this.trafficBannerEl = document.getElementById('trafficBanner');
        this.initWebSocket();
        this.initMap();
        this.initEventListeners();
        this.startClock();
        this.updateSystemStatus();
        this.initAircraftTabs();
        this.startTrafficWatchdog();
    }

    markTraffic() {
        this.lastMessageAt = Date.now();
        if (this.trafficBannerEl) {
            this.trafficBannerEl.classList.remove('visible');
        }
    }

    startTrafficWatchdog() {
        const NO_TRAFFIC_MS = 5000; // 5 seconds
        this.lastMessageAt = 0;
        if (this.trafficTimer) {
            clearInterval(this.trafficTimer);
        }
        this.trafficTimer = setInterval(() => {
            const now = Date.now();
            const hasTraffic = this.lastMessageAt && (now - this.lastMessageAt) < NO_TRAFFIC_MS;
            if (!hasTraffic) {
                if (this.trafficBannerEl) {
                    this.trafficBannerEl.classList.add('visible');
                }
            }
        }, 1000);
    }

    initAircraftTabs() {
        // Initialize aircraft tabs
        const tabs = document.querySelectorAll('.aircraft-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const aircraftId = parseInt(e.target.dataset.aircraft);
                this.switchAircraftTab(aircraftId);
            });
        });
    }

    switchAircraftTab(aircraftId) {
        // Switch active tab
        document.querySelectorAll('.aircraft-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.aircraft-data').forEach(data => {
            data.classList.remove('active');
        });

        // Add null check
        const tabElement = document.querySelector(`[data-aircraft="${aircraftId}"]`);
        const dataElement = document.getElementById(`aircraftData${aircraftId}`);
        
        if (tabElement) {
            tabElement.classList.add('active');
        } else {
            console.warn(`Tab element not found for aircraft: ${aircraftId}`);
        }
        
        if (dataElement) {
            dataElement.classList.add('active');
        } else {
            console.warn(`Data element not found for aircraft: ${aircraftId}`);
        }
        
        this.currentAircraftTab = aircraftId;
        
        // Show data if available for this aircraft
        if (this.aircraftData.has(aircraftId)) {
            this.updateAircraftTabData(aircraftId, this.aircraftData.get(aircraftId));
        }
    }

    initWebSocket() {
        // WebSocket connection options
        const socketOptions = {
            transports: ['websocket', 'polling'],
            timeout: 20000,
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5,
            maxReconnectionAttempts: 10
        };
        
        this.socket = io(socketOptions);
        
        this.socket.on('connect', () => {
            console.log('WebSocket connection established');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket connection closed:', reason);
            this.updateConnectionStatus(false);
        });

        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.updateConnectionStatus(false);
        });

        // Listen to all aircraft data
        this.socket.on('aircraftData', (data) => {
            this.markTraffic();
            this.handleAircraftData(data);
        });

        this.socket.on('intelligence', (data) => {
            this.markTraffic();
            this.handleIntelligenceData(data);
        });

        this.socket.on('messaging', (data) => {
            this.markTraffic();
            this.handleMessagingData(data);
        });
    }

    initMap() {
        // Default coordinates (Ankara) - used if geolocation is not available
        const defaultCoords = [39.9334, 32.8597];
        const defaultZoom = 12;
        
        // Initialize map with default coordinates first
        this.map = L.map('map').setView(defaultCoords, defaultZoom);
        
        // Default satellite layer
        this.satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Military Command Control System'
        });

        // Street layer
        this.streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Military Command Control System'
        });

        // Add default layer
        this.satelliteLayer.addTo(this.map);
        
        // Try to get user's location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    // Success: Use user's location
                    const userLat = position.coords.latitude;
                    const userLon = position.coords.longitude;
                    this.map.setView([userLat, userLon], defaultZoom);
                },
                (error) => {
                    // Error: Use default location (Ankara)
                    console.log('Geolocation not available, using default location (Ankara)');
                    this.map.setView(defaultCoords, defaultZoom);
                }
            );
        } else {
            // Geolocation not supported: Use default location (Ankara)
            console.log('Geolocation not supported, using default location (Ankara)');
            this.map.setView(defaultCoords, defaultZoom);
        }

        // Custom map controls styling
        this.map.zoomControl.setPosition('topright');
        
        // Flag to track if map has been initially centered on aircraft
        this.mapCenteredOnAircraft = false;
    }

    initEventListeners() {
        // Map control buttons
        document.getElementById('satelliteBtn').addEventListener('click', () => {
            this.switchMapMode('satellite');
        });

        document.getElementById('streetBtn').addEventListener('click', () => {
            this.switchMapMode('street');
        });

        document.getElementById('dayNightBtn').addEventListener('click', () => {
            this.toggleDayNight();
        });

        // Collapsible data panels (left-side list remains, headers toggle content)
        const dataPanels = Array.from(document.querySelectorAll('.right-panel .data-panel'));
        document.querySelectorAll('.right-panel .data-panel .panel-header').forEach(header => {
            header.addEventListener('click', () => {
                const panel = header.parentElement;
                const content = header.nextElementSibling;
                if (!panel || !content) return;
                const isExpanded = panel.classList.contains('expanded');
                // Collapse all
                dataPanels.forEach(p => {
                    p.classList.remove('expanded');
                    const pc = p.querySelector('.panel-content');
                    if (pc) pc.classList.add('collapsed');
                });
                // Toggle current
                if (!isExpanded) {
                    panel.classList.add('expanded');
                    content.classList.remove('collapsed');
                } else {
                    panel.classList.remove('expanded');
                    content.classList.add('collapsed');
                }
            });
        });

        // Aircraft group flyout toggle
        const groupHeader = document.querySelector('.aircraft-group-flyout .group-header');
        const groupContent = document.querySelector('.aircraft-group-flyout .group-content');
        if (groupHeader && groupContent) {
            groupHeader.addEventListener('click', () => {
                groupContent.classList.toggle('collapsed');
            });
        }
    }

    switchMapMode(mode) {
        // Remove active class from all buttons
        document.querySelectorAll('.map-btn').forEach(btn => btn.classList.remove('active'));
        
        // Remove current layer
        this.map.removeLayer(this.satelliteLayer);
        this.map.removeLayer(this.streetLayer);

        if (mode === 'satellite') {
            this.satelliteLayer.addTo(this.map);
            const satelliteBtn = document.getElementById('satelliteBtn');
            if (satelliteBtn) {
                satelliteBtn.classList.add('active');
            }
        } else if (mode === 'street') {
            this.streetLayer.addTo(this.map);
            const streetBtn = document.getElementById('streetBtn');
            if (streetBtn) {
                streetBtn.classList.add('active');
            }
        }

        this.currentMapMode = mode;
        this.applyNightMode();
    }

    toggleDayNight() {
        this.isDayMode = !this.isDayMode;
        const btn = document.getElementById('dayNightBtn');
        const icon = btn.querySelector('i');
        const text = btn.querySelector('span');

        if (this.isDayMode) {
            icon.className = 'fas fa-sun';
            text.textContent = 'DAY';
        } else {
            icon.className = 'fas fa-moon';
            text.textContent = 'NIGHT';
        }

        this.applyNightMode();
    }

    applyNightMode() {
        const mapContainer = document.getElementById('map');
        if (this.isDayMode) {
            mapContainer.classList.remove('night-mode');
        } else {
            mapContainer.classList.add('night-mode');
        }
    }

    handleAircraftData(data) {
        // Store aircraft data
        this.aircraftData.set(data.id, data);
        
        // Update aircraft group status
        this.updateAircraftGroupStatus(true);
        
        // Update data for aircraft in active tab
        this.updateAircraftTabData(data.id, data);
        
        // Update aircraft on map
        this.updateAircraftOnMap(data);
        
        // Aircraft info panel removed; no separate update needed
    }

    updateAircraftGroupStatus(active) {
        const statusElement = document.getElementById('aircraftGroupStatus');
        if (statusElement) {
            statusElement.className = active ? 'status-dot active' : 'status-dot';
        }
    }

    updateAircraftTabData(aircraftId, data) {
        const contentElement = document.getElementById(`aircraftData${aircraftId}`);
        if (contentElement) {
            const formattedData = this.formatAircraftData(data);
            contentElement.innerHTML = formattedData;
        }
    }

    formatAircraftData(data) {
        const isOwnAircraft = data.isOwnAircraft ? ' (MAIN AIRCRAFT)' : '';
        const orientationDeg = (data.orientation_degrees !== undefined && data.orientation_degrees !== null)
            ? data.orientation_degrees
            : (data.heading !== undefined ? data.heading : undefined);
        const speedKmh = (data.speed_kmh !== undefined && data.speed_kmh !== null)
            ? data.speed_kmh
            : (data.speed_mps !== undefined ? (data.speed_mps * 3.6) : undefined);
        const timeSec = (data.time_seconds !== undefined && data.time_seconds !== null)
            ? data.time_seconds
            : (data.time !== undefined ? data.time : undefined);
        return `
            <div class="data-item">
                <span class="data-label">Callsign:</span>
                <span class="data-value">${data.callsign}${isOwnAircraft}</span>
            </div>
            <div class="data-item">
                <span class="data-label">Location:</span>
                <span class="data-value">${data.latitude.toFixed(6)}, ${data.longitude.toFixed(6)}</span>
            </div>
            <div class="data-item">
                <span class="data-label">Altitude:</span>
                <span class="data-value">${data.altitude} m</span>
            </div>
            <div class="data-item">
                <span class="data-label">Speed:</span>
                <span class="data-value">${speedKmh !== undefined ? speedKmh.toFixed(1) : '--'} km/h</span>
            </div>
            <div class="data-item">
                <span class="data-label">Heading:</span>
                <span class="data-value">${orientationDeg !== undefined ? orientationDeg : '--'}°</span>
            </div>
            <div class="data-item">
                <span class="data-label">Time:</span>
                <span class="data-value">${timeSec !== undefined ? new Date(timeSec * 1000).toLocaleTimeString('tr-TR') : '--'}</span>
            </div>
        `;
    }

    handleIntelligenceData(data) {
        this.updateDataPanel('intelligenceContent', 'intelligenceStatus', data, 'INTELLIGENCE');
        
        // Process target detection with proper location data
        if (data.latitude && data.longitude) {
            this.processTargetDetection({
                ...data,
                td_target_id: data.td_target_id || data.td_target_ID,
                td_latitude: data.latitude,
                td_longitude: data.longitude,
                td_altitude: data.altitude
            });
        }
        
        this.updateMapMarkers(data);
    }

    handleMessagingData(data) {
        this.updateDataPanel('messagingContent', 'messagingStatus', data, 'MESSAGING');
        
        // Add messaging location markers if available
        if (data.latitude && data.longitude) {
            this.addMessagingMarker(data);
        }
        
        // Add task assignment location markers
        if (data.tc_assignment_location_latitude && data.tc_assignment_location_longitude) {
            this.addTaskAssignmentMarker(data);
        }
        
        // Add critical detection location markers
        if (data.cd_detection_latitude && data.cd_detection_longitude) {
            this.addCriticalDetectionMarker(data);
        }
    }

    updateDataPanel(contentId, statusId, data, type) {
        const content = document.getElementById(contentId);
        const status = document.getElementById(statusId);
        
        // Update status indicator
        status.classList.add('active');
        setTimeout(() => status.classList.remove('active'), 1000);

        // Create data item
        const dataItem = document.createElement('div');
        dataItem.className = 'data-item';
        
        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = new Date().toLocaleTimeString('tr-TR');
        
        const dataContent = document.createElement('div');
        dataContent.className = 'content';
        
        // Format data based on type
        if (type === 'CORE DATA') {
            dataContent.innerHTML = this.formatCoreData(data);
        } else if (type === 'INTELLIGENCE') {
            dataContent.innerHTML = this.formatIntelligenceData(data);
        } else if (type === 'MESSAGING') {
            dataContent.innerHTML = this.formatMessagingData(data);
        }

        dataItem.appendChild(timestamp);
        dataItem.appendChild(dataContent);

        // Add to panel and limit items
        if (content.querySelector('.no-data')) {
            content.innerHTML = '';
        }
        
        content.insertBefore(dataItem, content.firstChild);
        
        // Keep only last 5 items
        while (content.children.length > 5) {
            content.removeChild(content.lastChild);
        }
    }

    formatCoreData(data) {
        return `
            <div class="data-field"><span class="label">Latitude:</span><span class="value">${data.latitude?.toFixed(6) || 'N/A'}</span></div>
            <div class="data-field"><span class="label">Longitude:</span><span class="value">${data.longitude?.toFixed(6) || 'N/A'}</span></div>
            <div class="data-field"><span class="label">Altitude:</span><span class="value">${data.altitude?.toFixed(2) || 'N/A'} m</span></div>
            <div class="data-field"><span class="label">Speed:</span><span class="value">${data.speed?.toFixed(2) || 'N/A'} km/h</span></div>
            <div class="data-field"><span class="label">Heading:</span><span class="value">${data.heading?.toFixed(1) || 'N/A'}°</span></div>
        `;
    }

    formatIntelligenceData(data) {
        let html = '';
        
        // Vehicle Status data
        if (data.vs_mission_status || data.vs_task_status !== undefined) {
            const mission = data.vs_mission_status || data.vs_task_status;
            html += `<div class="data-field"><span class="label">Mission Status:</span><span class="value">${mission}</span></div>`;
        }
        if (data.vs_battery_level !== undefined) {
            html += `<div class="data-field"><span class="label">Battery:</span><span class="value">${data.vs_battery_level}%</span></div>`;
        }
        if (data.vs_battery_percentage !== undefined) {
            html += `<div class="data-field"><span class="label">Battery (%):</span><span class="value">${data.vs_battery_percentage}%</span></div>`;
        }
        if (data.vs_signal_strength_dbm !== undefined) {
            html += `<div class="data-field"><span class="label">Signal Strength:</span><span class="value">${data.vs_signal_strength_dbm} dBm</span></div>`;
        }
        if (data.vs_system_error !== undefined) {
            html += `<div class="data-field"><span class="label">System Error:</span><span class="value">${data.vs_system_error ? 'Yes' : 'No'}</span></div>`;
        }
        
        // Target Detection data
        if (data.td_target_id || data.td_target_ID) {
            const targetId = data.td_target_id || data.td_target_ID;
            html += `<div class="data-field"><span class="label">Target ID:</span><span class="value">${targetId}</span></div>`;
        }
        if (data.td_target_type !== undefined) {
            const targetTypes = {1: 'Military Vehicle', 2: 'Civilian Aircraft', 3: 'Ship', 4: 'Personnel', 5: 'Area'};
            html += `<div class="data-field"><span class="label">Target Type:</span><span class="value">${targetTypes[data.td_target_type] || 'Unknown'}</span></div>`;
        }
        if (data.td_location_latitude && data.td_location_longitude) {
            html += `<div class="data-field"><span class="label">Target Location:</span><span class="value">${data.td_location_latitude.toFixed(6)}, ${data.td_location_longitude.toFixed(6)}</span></div>`;
        }
        if (data.td_confidence_level !== undefined) {
            html += `<div class="data-field"><span class="label">Confidence Level:</span><span class="value">${(data.td_confidence_level * 100).toFixed(1)}%</span></div>`;
        }
        if (data.td_description) {
            html += `<div class="data-field"><span class="label">Description:</span><span class="value">${data.td_description}</span></div>`;
        }
        if (data.td_raw_data_link) {
            html += `<div class="data-field"><span class="label">Raw Data:</span><span class="value">${data.td_raw_data_link}</span></div>`;
        }
        
        // Task Assignment data
        if (data.ta_command) {
            html += `<div class="data-field"><span class="label">Task Command:</span><span class="value">${data.ta_command}</span></div>`;
        }
        if (data.ta_location_latitude && data.ta_location_longitude) {
            html += `<div class="data-field"><span class="label">Task Location:</span><span class="value">${data.ta_location_latitude.toFixed(6)}, ${data.ta_location_longitude.toFixed(6)}</span></div>`;
        }
        if (data.ta_location_speed_mps !== undefined) {
            html += `<div class="data-field"><span class="label">Task Speed (m/s):</span><span class="value">${data.ta_location_speed_mps}</span></div>`;
        }
        if (data.ta_location_orientation_degrees !== undefined) {
            html += `<div class="data-field"><span class="label">Task Heading (°):</span><span class="value">${data.ta_location_orientation_degrees}</span></div>`;
        }
        
        return html || '<div class="data-field"><span class="value">Processing data...</span></div>';
    }

    formatMessagingData(data) {
        let html = '';
        
        // Message type
        const messageTypes = {1: 'Status Report', 2: 'Critical Detection', 3: 'Task Command'};
        html += `<div class="data-field"><span class="label">Message Type:</span><span class="value">${messageTypes[data.message_type] || 'Unknown'}</span></div>`;
        
        // Status Report data
        if (data.sr_sender_id) {
            html += `<div class="data-field"><span class="label">Sender ID:</span><span class="value">${data.sr_sender_id}</span></div>`;
        }
        if (data.sr_timestamp !== undefined) {
            html += `<div class="data-field"><span class="label">Timestamp:</span><span class="value">${data.sr_timestamp}</span></div>`;
        }
        if (data.sr_status !== undefined) {
            const statusTypes = {1: 'Active', 2: 'Standby', 3: 'On Mission', 4: 'Returning'};
            html += `<div class="data-field"><span class="label">Status:</span><span class="value">${statusTypes[data.sr_status] || 'Unknown'}</span></div>`;
        }
        if (data.sr_battery_level !== undefined) {
            html += `<div class="data-field"><span class="label">Battery:</span><span class="value">${data.sr_battery_level}%</span></div>`;
        }
        if (data.sr_fuel_level !== undefined) {
            html += `<div class="data-field"><span class="label">Fuel:</span><span class="value">${data.sr_fuel_level}%</span></div>`;
        }
        if (data.sr_system_health !== undefined) {
            html += `<div class="data-field"><span class="label">System Health:</span><span class="value">${data.sr_system_health ? 'Good' : 'Issue'}</span></div>`;
        }
        if (data.sr_location_latitude && data.sr_location_longitude) {
            html += `<div class="data-field"><span class="label">Location:</span><span class="value">${data.sr_location_latitude.toFixed(6)}, ${data.sr_location_longitude.toFixed(6)}</span></div>`;
        }
        if (data.sr_location_speed_mps !== undefined) {
            html += `<div class="data-field"><span class="label">Speed (m/s):</span><span class="value">${data.sr_location_speed_mps}</span></div>`;
        }
        if (data.sr_location_orientation_degrees !== undefined) {
            html += `<div class="data-field"><span class="label">Heading (°):</span><span class="value">${data.sr_location_orientation_degrees}</span></div>`;
        }
        
        // Critical Detection data
        if (data.cd_target_id || data.cd_target_ID) {
            const targetId = data.cd_target_id || data.cd_target_ID;
            html += `<div class="data-field"><span class="label">Critical Target:</span><span class="value">${targetId}</span></div>`;
        }
        if (data.cd_target_type !== undefined) {
            const targetTypes = {1: 'Military Vehicle', 2: 'Civilian Aircraft', 3: 'Ship', 4: 'Personnel', 5: 'Area'};
            html += `<div class="data-field"><span class="label">Target Type:</span><span class="value">${targetTypes[data.cd_target_type] || 'Unknown'}</span></div>`;
        }
        if (data.cd_confidence_level !== undefined) {
            html += `<div class="data-field"><span class="label">Confidence Level:</span><span class="value">${(data.cd_confidence_level * 100).toFixed(1)}%</span></div>`;
        }
        if (data.cd_description) {
            html += `<div class="data-field"><span class="label">Description:</span><span class="value">${data.cd_description}</span></div>`;
        }
        if (data.cd_raw_data_link) {
            html += `<div class="data-field"><span class="label">Raw Data:</span><span class="value">${data.cd_raw_data_link}</span></div>`;
        }
        if (data.cd_detection_latitude && data.cd_detection_longitude) {
            html += `<div class="data-field"><span class="label">Detection Location:</span><span class="value">${data.cd_detection_latitude.toFixed(6)}, ${data.cd_detection_longitude.toFixed(6)}</span></div>`;
        }
        if (data.cd_detection_speed_mps !== undefined) {
            html += `<div class="data-field"><span class="label">Detection Speed (m/s):</span><span class="value">${data.cd_detection_speed_mps}</span></div>`;
        }
        if (data.cd_detection_orientation_degrees !== undefined) {
            html += `<div class="data-field"><span class="label">Detection Heading (°):</span><span class="value">${data.cd_detection_orientation_degrees}</span></div>`;
        }
        // Secondary Detection Location (scenario optional set)
        if (data.cd_detection_location_data_latitude && data.cd_detection_location_data_longitude) {
            html += `<div class="data-field"><span class="label">Detection Location (2):</span><span class="value">${data.cd_detection_location_data_latitude.toFixed(6)}, ${data.cd_detection_location_data_longitude.toFixed(6)}</span></div>`;
        }
        if (data.cd_detection_location_data_speed_mps !== undefined) {
            html += `<div class="data-field"><span class="label">Detection Speed (2) (m/s):</span><span class="value">${data.cd_detection_location_data_speed_mps}</span></div>`;
        }
        if (data.cd_detection_location_data_orientation_degrees !== undefined) {
            html += `<div class="data-field"><span class="label">Detection Heading (2) (°):</span><span class="value">${data.cd_detection_location_data_orientation_degrees}</span></div>`;
        }
        
        // Task Command data
        if (data.tc_command || data.tc_assignment_command) {
            const command = data.tc_command || data.tc_assignment_command;
            html += `<div class="data-field"><span class="label">Task Command:</span><span class="value">${command}</span></div>`;
        }
        if (data.tc_receiver_id) {
            html += `<div class="data-field"><span class="label">Receiver ID:</span><span class="value">${data.tc_receiver_id}</span></div>`;
        }
        if (data.tc_assignment_location_latitude && data.tc_assignment_location_longitude) {
            html += `<div class="data-field"><span class="label">Task Location:</span><span class="value">${data.tc_assignment_location_latitude.toFixed(6)}, ${data.tc_assignment_location_longitude.toFixed(6)}</span></div>`;
        }
        if (data.tc_assignment_location_speed_mps !== undefined) {
            html += `<div class="data-field"><span class="label">Task Speed (m/s):</span><span class="value">${data.tc_assignment_location_speed_mps}</span></div>`;
        }
        if (data.tc_assignment_location_orientation_degrees !== undefined) {
            html += `<div class="data-field"><span class="label">Task Heading (°):</span><span class="value">${data.tc_assignment_location_orientation_degrees}</span></div>`;
        }
        // Secondary Task Target Location (scenario optional set)
        if (data.tc_assignment_target_location_data_latitude && data.tc_assignment_target_location_data_longitude) {
            html += `<div class="data-field"><span class="label">Target Location (2):</span><span class="value">${data.tc_assignment_target_location_data_latitude.toFixed(6)}, ${data.tc_assignment_target_location_data_longitude.toFixed(6)}</span></div>`;
        }
        if (data.tc_assignment_target_location_data_speed_mps !== undefined) {
            html += `<div class="data-field"><span class="label">Target Speed (2) (m/s):</span><span class="value">${data.tc_assignment_target_location_data_speed_mps}</span></div>`;
        }
        if (data.tc_assignment_target_location_data_orientation_degrees !== undefined) {
            html += `<div class="data-field"><span class="label">Target Heading (2) (°):</span><span class="value">${data.tc_assignment_target_location_data_orientation_degrees}</span></div>`;
        }
        
        return html;
    }

    updateAircraftOnMap(data) {
        if (data.latitude && data.longitude) {
            const lat = data.latitude;
            const lon = data.longitude;
            const markerId = `aircraft_${data.id}`;
            
            // Remove old marker
            if (this.markers.has(markerId)) {
                this.map.removeLayer(this.markers.get(markerId));
            }
            
            // Determine style based on aircraft type
            const isOwnAircraft = data.isOwnAircraft;
            const className = isOwnAircraft ? 'military-marker own-aircraft' : 'military-marker wingman-aircraft';
            
            // Create aircraft icon
            const icon = L.divIcon({
                className: className,
                html: '<i class="fas fa-fighter-jet"></i>',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });
            
            // Create new marker
            const marker = L.marker([lat, lon], { icon })
                .addTo(this.map)
                .bindPopup(`
                    <div style="color: #000;">
                        <strong>${data.callsign}${isOwnAircraft ? ' (Main Aircraft)' : ''}</strong><br>
                        Latitude: ${lat.toFixed(6)}<br>
                        Longitude: ${lon.toFixed(6)}<br>
                        Altitude: ${data.altitude?.toFixed(2) || 'N/A'} m<br>
                        Speed: ${(data.speed_kmh !== undefined ? data.speed_kmh.toFixed(2) : (data.speed_mps !== undefined ? (data.speed_mps*3.6).toFixed(2) : 'N/A'))} km/h<br>
                        Orientation: ${(data.orientation_degrees !== undefined ? data.orientation_degrees : (data.heading !== undefined ? data.heading : 'N/A'))}°
                    </div>
                `);
            
            // Add marker to markers Map
            this.markers.set(markerId, marker);
            
            console.log(`${data.callsign} position updated: ${lat.toFixed(6)}, ${lon.toFixed(6)}`);
        }
    }



    updateAircraftInfo(data) {
        document.getElementById('aircraftLat').textContent = data.latitude?.toFixed(6) || '--';
        document.getElementById('aircraftLon').textContent = data.longitude?.toFixed(6) || '--';
        document.getElementById('aircraftAlt').textContent = data.altitude ? `${data.altitude.toFixed(2)} m` : '--';
        document.getElementById('aircraftSpeed').textContent = data.speed ? `${data.speed.toFixed(2)} km/h` : '--';
        document.getElementById('aircraftHeading').textContent = data.heading ? `${data.heading.toFixed(1)}°` : '--';
    }

    processTargetDetection(data) {
        if (data.td_target_id && data.td_latitude && data.td_longitude) {
            const targetId = data.td_target_id;
            const target = {
                id: targetId,
                type: data.td_target_type || 'Unknown',
                lat: data.td_latitude,
                lon: data.td_longitude,
                confidence: data.td_confidence_level || 0,
                description: data.td_description || '',
                timestamp: new Date()
            };
            
            this.targets.set(targetId, target);
            this.updateTargetsList();
            this.addTargetMarker(target);
        }
    }

    updateTargetsList() {
        const targetList = document.getElementById('targetList');
        
        if (this.targets.size === 0) {
            targetList.innerHTML = '<div class="no-data">No targets detected</div>';
            return;
        }
        
        targetList.innerHTML = '';
        
        Array.from(this.targets.values())
            .sort((a, b) => b.timestamp - a.timestamp)
            .slice(0, 10)
            .forEach(target => {
                const targetItem = document.createElement('div');
                targetItem.className = 'target-item';
                targetItem.innerHTML = `
                    <div class="target-id">TARGET: ${target.id}</div>
                    <div class="target-info">
                        <div><span style="color: #aaa;">Type:</span> ${target.type}</div>
                        <div><span style="color: #aaa;">Confidence:</span> ${target.confidence}%</div>
                        <div><span style="color: #aaa;">Latitude:</span> ${target.lat.toFixed(4)}</div>
                        <div><span style="color: #aaa;">Longitude:</span> ${target.lon.toFixed(4)}</div>
                    </div>
                `;
                targetList.appendChild(targetItem);
            });
    }

    addTargetMarker(target) {
        const markerId = `target_${target.id}`;
        
        // Remove existing marker if exists
        if (this.markers.has(markerId)) {
            this.map.removeLayer(this.markers.get(markerId));
        }
        
        let iconClass = 'military-marker';
        let iconSymbol = 'fas fa-crosshairs';
        
        // Determine icon based on target type
        switch ((target.type || '').toString().toLowerCase()) {
            case 'aircraft':
                iconClass += ' aircraft';
                iconSymbol = 'fas fa-plane';
                break;
            case 'ship':
                iconClass += ' ship';
                iconSymbol = 'fas fa-ship';
                break;
            case 'tank':
                iconClass += ' tank';
                iconSymbol = 'fas fa-tank';
                break;
            case 'base':
            case 'karargah':
                iconClass += ' base';
                iconSymbol = 'fas fa-flag';
                break;
        }
        
        const icon = L.divIcon({
            className: iconClass,
            html: `<i class="${iconSymbol}"></i>`,
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        const marker = L.marker([target.lat, target.lon], { icon })
            .addTo(this.map)
            .bindPopup(`
                <div style="color: #000;">
                    <strong>${target.type} - ${target.id}</strong><br>
                    Confidence Level: ${target.confidence}%<br>
                    Latitude: ${target.lat.toFixed(6)}<br>
                    Longitude: ${target.lon.toFixed(6)}<br>
                    ${target.description ? `Description: ${target.description}` : ''}
                </div>
            `);
        
        this.markers.set(markerId, marker);
    }

    updateMapMarkers(data) {
        // This method can be extended to handle other types of markers
        // based on different data sources
    }

    addMessagingMarker(data) {
        const markerId = `messaging_${Date.now()}`;
        
        const icon = L.divIcon({
            className: 'military-marker messaging',
            html: '<i class="fas fa-comments"></i>',
            iconSize: [25, 25],
            iconAnchor: [12, 12]
        });
        
        const marker = L.marker([data.latitude, data.longitude], { icon })
            .addTo(this.map)
            .bindPopup(`
                <div style="color: #000;">
                    <strong>Message Location</strong><br>
                    Sender: ${data.sr_sender_id || 'Unknown'}<br>
                    Status: ${data.sr_status || 'Unknown'}<br>
                    Latitude: ${data.latitude.toFixed(6)}<br>
                    Longitude: ${data.longitude.toFixed(6)}
                </div>
            `);
        
        this.markers.set(markerId, marker);
    }

    addTaskAssignmentMarker(data) {
        const markerId = `task_${Date.now()}`;
        
        const icon = L.divIcon({
            className: 'military-marker task',
            html: '<i class="fas fa-tasks"></i>',
            iconSize: [25, 25],
            iconAnchor: [12, 12]
        });
        
        const marker = L.marker([data.tc_assignment_location_latitude, data.tc_assignment_location_longitude], { icon })
            .addTo(this.map)
            .bindPopup(`
                <div style="color: #000;">
                    <strong>Task Location</strong><br>
                    Receiver: ${data.tc_receiver_id || 'Unknown'}<br>
                    Command: ${data.tc_assignment_command || data.tc_command || 'Unknown'}<br>
                    Latitude: ${data.tc_assignment_location_latitude.toFixed(6)}<br>
                    Longitude: ${data.tc_assignment_location_longitude.toFixed(6)}
                </div>
            `);
        
        this.markers.set(markerId, marker);
    }

    addCriticalDetectionMarker(data) {
        const markerId = `critical_${Date.now()}`;
        
        const icon = L.divIcon({
            className: 'military-marker critical',
            html: '<i class="fas fa-exclamation-triangle"></i>',
            iconSize: [25, 25],
            iconAnchor: [12, 12]
        });
        
        const marker = L.marker([data.cd_detection_latitude, data.cd_detection_longitude], { icon })
            .addTo(this.map)
            .bindPopup(`
                <div style="color: #000;">
                    <strong>Critical Detection</strong><br>
                    Target ID: ${data.cd_target_id || data.cd_target_ID || 'Unknown'}<br>
                    Target Type: ${data.cd_target_type || 'Unknown'}<br>
                    Confidence: ${data.cd_confidence_level || 'Unknown'}%<br>
                    Latitude: ${data.cd_detection_latitude.toFixed(6)}<br>
                    Longitude: ${data.cd_detection_longitude.toFixed(6)}
                </div>
            `);
        
        this.markers.set(markerId, marker);
    }

    updateConnectionStatus(connected) {
        const systemStatus = document.getElementById('systemStatus');
        if (connected) {
            systemStatus.classList.add('active');
        } else {
            systemStatus.classList.remove('active');
        }
    }

    updateSystemStatus() {
        // Simulate system status updates
        setInterval(() => {
            const panels = ['coreDataStatus', 'intelligenceStatus', 'messagingStatus'];
            panels.forEach(panelId => {
                const panel = document.getElementById(panelId);
                if (panel && Math.random() > 0.7) {
                    panel.classList.add('active');
                    setTimeout(() => {
                        if (panel) {
                            panel.classList.remove('active');
                        }
                    }, 500);
                }
            });
        }, 3000);
    }

    startClock() {
        const updateTime = () => {
            const now = new Date();
            const timeString = now.toLocaleString('tr-TR', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            document.getElementById('currentTime').textContent = timeString;
        };
        
        updateTime();
        setInterval(updateTime, 1000);
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new MilitaryDashboard();
});