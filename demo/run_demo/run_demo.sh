#!/bin/bash
# Military Command Control System - Demo Launcher (Linux Version)
# Linux equivalent of Windows run_demo.bat file

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Set terminal title
echo -e "\033]0;Military Command Control System - Demo Launcher\007"

echo -e "${CYAN}"
echo "========================================"
echo "   MILITARY COMMAND CONTROL SYSTEM"
echo "   Demo Launcher v1.0 (Linux)"
echo "========================================"
echo -e "${NC}"
echo

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}[WARNING] Node.js not found!${NC}"
    echo -e "${YELLOW}Only DDS Publishers will be started.${NC}"
    echo "Node.js installation required for web dashboard:"
    echo "For Ubuntu/Debian: sudo apt install nodejs npm"
    echo
    NODEJS_AVAILABLE=false
else
    echo -e "${GREEN}Node.js found: $(node --version)${NC}"
    NODEJS_AVAILABLE=true
fi

# Navigate to demo directory and detect project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$DEMO_DIR")"

# Walk up to find project root (contains IDL and scenarios)
CURRENT_DIR="$DEMO_DIR"
while [ "$CURRENT_DIR" != "/" ] && [ "$CURRENT_DIR" != "." ]; do
    if [ -d "$CURRENT_DIR/IDL" ] && [ -d "$CURRENT_DIR/scenarios" ]; then
        PROJECT_ROOT="$CURRENT_DIR"
        break
    fi
    CURRENT_DIR="$(dirname "$CURRENT_DIR")"
done

cd "$DEMO_DIR"

echo "Demo directory: $DEMO_DIR"
echo "Project root: $PROJECT_ROOT"

# Install dependencies if node_modules doesn't exist
if [ "$NODEJS_AVAILABLE" = true ] && [ ! -d "$DEMO_DIR/node_modules" ]; then
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    cd "$DEMO_DIR"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Dependency installation failed!${NC}"
        echo -e "${YELLOW}Only DDS Publishers will be started.${NC}"
        NODEJS_AVAILABLE=false
    else
        echo -e "${GREEN}Dependencies installed successfully.${NC}"
        echo
    fi
elif [ "$NODEJS_AVAILABLE" = false ]; then
    echo -e "${YELLOW}Skipping dependencies (Node.js not available)...${NC}"
fi

# Create PID file to track processes
echo "" > "$DEMO_DIR/processes.pid"

echo -e "${BLUE}Starting system...${NC}"
echo

# Function to start a process and track its PID
start_process() {
    local title="$1"
    local command="$2"
    local working_dir="$3"
    
    if [ -n "$working_dir" ]; then
        cd "$working_dir"
    fi
    
    # Start process in background and capture PID
    eval "$command" &
    local pid=$!
    echo "$title PID: $pid" >> "$DEMO_DIR/processes.pid"
    echo -e "${GREEN}[OK] $title started (PID: $pid)${NC}"
    
    # Return to original directory
    cd "$DEMO_DIR"
}

# Start the Node.js backend server
if [ "$NODEJS_AVAILABLE" = true ]; then
    echo -e "${YELLOW}[1/4] Starting backend server...${NC}"
    start_process "Backend Server" "node server.js" "$DEMO_DIR"
    sleep 3
else
    echo -e "${YELLOW}[1/4] Backend server skipped (Node.js not available)...${NC}"
fi

# DDS Publishers are started manually via separate scripts
echo -e "${YELLOW}[2/4] DDS Publishers will be started manually...${NC}"
echo -e "${CYAN}Use the following scripts for DDS Publishers:${NC}"
echo "- CoreData Publisher: $PROJECT_ROOT/IDL/CoreData_idl_generated/CoreDatamain publisher"
echo "- Intelligence Publisher: $PROJECT_ROOT/IDL/Intelligence_idl_generated/Intelligencemain publisher"  
echo "- Messaging Publisher: $PROJECT_ROOT/IDL/Messaging_idl_generated/Messagingmain publisher"
echo "- Monitor: $PROJECT_ROOT/monitoring/run_monitoring/run_monitoring.sh"
echo

echo
echo -e "${GREEN}Demo frontend started!${NC}"
echo
echo -e "${CYAN}System status checks:${NC}"
if [ "$NODEJS_AVAILABLE" = true ]; then
    echo "- Backend Server: http://localhost:3000"
    echo "- WebSocket Connection: ws://localhost:3000"
    echo "- DDS Monitor: Will be started manually"
fi
echo "- DDS Publishers: Will be started manually"
echo

# Wait a bit more for all services to start
if [ "$NODEJS_AVAILABLE" = true ]; then
    echo -e "${YELLOW}Opening web browser...${NC}"
    sleep 3

    # Open the web browser
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:3000" &
    elif command -v firefox &> /dev/null; then
        firefox "http://localhost:3000" &
    elif command -v google-chrome &> /dev/null; then
        google-chrome "http://localhost:3000" &
    elif command -v chromium-browser &> /dev/null; then
        chromium-browser "http://localhost:3000" &
    else
        echo -e "${YELLOW}[WARNING] Web browser not found. Please open http://localhost:3000 manually.${NC}"
    fi
else
    echo -e "${YELLOW}Web dashboard unavailable (Node.js not available)${NC}"
    echo -e "${YELLOW}Only DDS Publishers are running.${NC}"
fi

echo
echo -e "${CYAN}========================================"
echo "   SYSTEM ACTIVE"
echo "========================================"
echo -e "${NC}"
echo -e "${GREEN}Website opened in your browser.${NC}"
echo -e "${CYAN}To see DDS data, start monitor and publishers manually.${NC}"
echo -e "${RED}DO NOT CLOSE this window while demo is running!${NC}"
echo
echo -e "${YELLOW}Press any key to close demo...${NC}"
read -n 1

# Cleanup section
echo
echo -e "${YELLOW}Shutting down system...${NC}"
echo

# Function to kill process by PID
kill_process() {
    local pid="$1"
    local name="$2"
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null
        echo -e "${GREEN}[OK] $name closed${NC}"
    else
        echo -e "${YELLOW}[WARNING] $name already closed${NC}"
    fi
}

# Kill all processes from PID file
if [ -f "$DEMO_DIR/processes.pid" ]; then
    echo -e "${YELLOW}[1/2] Closing demo processes...${NC}"
    while IFS= read -r line; do
        if [[ $line =~ ^(.+)\ PID:\ ([0-9]+)$ ]]; then
            name="${BASH_REMATCH[1]}"
            pid="${BASH_REMATCH[2]}"
            kill_process "$pid" "$name"
        fi
    done < "$DEMO_DIR/processes.pid"
fi

echo -e "${YELLOW}[2/2] Closing Node.js processes...${NC}"
pkill -f "node server.js" 2>/dev/null

# Clean up PID file
if [ -f "$DEMO_DIR/processes.pid" ]; then
    rm "$DEMO_DIR/processes.pid"
fi

# Kill any remaining Node.js processes on port 3000
PORT_PID=$(lsof -ti:3000 2>/dev/null)
if [ -n "$PORT_PID" ]; then
    echo -e "${YELLOW}Closing remaining processes on port 3000...${NC}"
    kill -9 $PORT_PID 2>/dev/null
fi

echo
echo -e "${GREEN}Demo closed.${NC}"
echo -e "${CYAN}DDS Publishers and Monitor may still be running.${NC}"
echo -e "${CYAN}You may need to close them manually.${NC}"
echo
if [ "$NODEJS_AVAILABLE" = false ]; then
    echo -e "${YELLOW}Note: Node.js installation required for web dashboard.${NC}"
    echo -e "${YELLOW}For Ubuntu/Debian: sudo apt install nodejs npm${NC}"
fi
echo
sleep 3
