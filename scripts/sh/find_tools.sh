#!/bin/bash
# Dynamic Finder - Linux Version
# Cross-platform tool detection for DDS project

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Dynamic Environment Finder - Linux Version ===${NC}"
echo "Detecting Python, Java, and CMake installations..."

# Initialize variables
PYTHON_PATH=""
JAVA_PATH=""
CMAKE_PATH=""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Python Detection
echo -e "\n${YELLOW}[INFO] Searching for Python installations...${NC}"

# Check system Python
if command_exists python3; then
    PYTHON_PATH=$(which python3)
    echo -e "${GREEN}[OK] System Python 3 found: $PYTHON_PATH${NC}"
elif command_exists python; then
    PYTHON_VERSION=$(python --version 2>&1)
    if [[ $PYTHON_VERSION == *"Python 3"* ]]; then
        PYTHON_PATH=$(which python)
        echo -e "${GREEN}[OK] System Python found: $PYTHON_PATH${NC}"
    fi
fi

# Check common Python installation paths
PYTHON_PATHS=(
    "/usr/bin/python3"
    "/usr/local/bin/python3"
    "/opt/python/bin/python3"
    "$HOME/.local/bin/python3"
    "/usr/bin/python3.12"
    "/usr/bin/python3.11"
    "/usr/bin/python3.10"
    "/usr/bin/python3.9"
)

for path in "${PYTHON_PATHS[@]}"; do
    if [[ -x "$path" && -z "$PYTHON_PATH" ]]; then
        PYTHON_PATH="$path"
        echo -e "${GREEN}[OK] Python found: $path${NC}"
        break
    fi
done

# Check Anaconda/Miniconda
if [[ -d "$HOME/anaconda3" && -x "$HOME/anaconda3/bin/python" ]]; then
    if [[ -z "$PYTHON_PATH" ]]; then
        PYTHON_PATH="$HOME/anaconda3/bin/python"
        echo -e "${GREEN}[OK] Anaconda Python found: $PYTHON_PATH${NC}"
    fi
fi

if [[ -d "$HOME/miniconda3" && -x "$HOME/miniconda3/bin/python" ]]; then
    if [[ -z "$PYTHON_PATH" ]]; then
        PYTHON_PATH="$HOME/miniconda3/bin/python"
        echo -e "${GREEN}[OK] Miniconda Python found: $PYTHON_PATH${NC}"
    fi
fi

if [[ -z "$PYTHON_PATH" ]]; then
    echo -e "${RED}[ERROR] Python not found!${NC}"
else
    echo -e "${GREEN}[SUCCESS] Using Python: $PYTHON_PATH${NC}"
fi

# Java Detection
echo -e "\n${YELLOW}[INFO] Searching for Java installations...${NC}"

if command_exists java; then
    JAVA_PATH=$(which java)
    echo -e "${GREEN}[OK] System Java found: $JAVA_PATH${NC}"
fi

# Check common Java installation paths
JAVA_PATHS=(
    "/usr/bin/java"
    "/usr/local/bin/java"
    "/opt/java/bin/java"
    "/usr/lib/jvm/default-java/bin/java"
    "/usr/lib/jvm/java-21-openjdk/bin/java"
    "/usr/lib/jvm/java-17-openjdk/bin/java"
    "/usr/lib/jvm/java-11-openjdk/bin/java"
    "/usr/lib/jvm/java-8-openjdk/bin/java"
)

for path in "${JAVA_PATHS[@]}"; do
    if [[ -x "$path" && -z "$JAVA_PATH" ]]; then
        JAVA_PATH="$path"
        echo -e "${GREEN}[OK] Java found: $path${NC}"
        break
    fi
done

if [[ -z "$JAVA_PATH" ]]; then
    echo -e "${RED}[ERROR] Java not found!${NC}"
else
    echo -e "${GREEN}[SUCCESS] Using Java: $JAVA_PATH${NC}"
fi

# CMake Detection
echo -e "\n${YELLOW}[INFO] Searching for CMake installations...${NC}"

if command_exists cmake; then
    CMAKE_PATH=$(which cmake)
    echo -e "${GREEN}[OK] System CMake found: $CMAKE_PATH${NC}"
fi

# Check common CMake installation paths
CMAKE_PATHS=(
    "/usr/bin/cmake"
    "/usr/local/bin/cmake"
    "/opt/cmake/bin/cmake"
    "/snap/cmake/current/bin/cmake"
)

for path in "${CMAKE_PATHS[@]}"; do
    if [[ -x "$path" && -z "$CMAKE_PATH" ]]; then
        CMAKE_PATH="$path"
        echo -e "${GREEN}[OK] CMake found: $path${NC}"
        break
    fi
done

if [[ -z "$CMAKE_PATH" ]]; then
    echo -e "${RED}[ERROR] CMake not found!${NC}"
else
    echo -e "${GREEN}[SUCCESS] Using CMake: $CMAKE_PATH${NC}"
fi

# Export environment variables
export DDS_PYTHON_PATH="$PYTHON_PATH"
export DDS_JAVA_PATH="$JAVA_PATH"
export DDS_CMAKE_PATH="$CMAKE_PATH"

# Create environment file for other scripts
ENV_FILE="$(dirname "$0")/export_environment_vars.sh"
cat > "$ENV_FILE" << EOF
#!/bin/bash
# DDS Environment Variables - Auto-generated
export DDS_PYTHON_PATH="$PYTHON_PATH"
export DDS_JAVA_PATH="$JAVA_PATH"
export DDS_CMAKE_PATH="$CMAKE_PATH"
EOF

echo -e "\n${BLUE}=== Environment Setup Complete ===${NC}"
echo -e "Environment variables exported and saved to: $ENV_FILE"

# Executable Detection
echo -e "\n${YELLOW}[INFO] Searching for DDS executables...${NC}"

# Find IDL generated executables
# Dynamically find project root (contains IDL and scenarios)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
CURRENT_DIR="$SCRIPT_DIR"
while [ "$CURRENT_DIR" != "/" ] && [ "$CURRENT_DIR" != "." ]; do
    if [ -d "$CURRENT_DIR/IDL" ] && [ -d "$CURRENT_DIR/scenarios" ]; then
        PROJECT_ROOT="$CURRENT_DIR"
        break
    fi
    CURRENT_DIR="$(dirname "$CURRENT_DIR")"
done
IDL_DIR="$PROJECT_ROOT/IDL"
if [[ -d "$IDL_DIR" ]]; then
    echo "Scanning IDL directory: $IDL_DIR"
    
    # Look for executables in Release and Debug directories
    for dir in "$IDL_DIR"/*_idl_generated; do
        if [[ -d "$dir" ]]; then
            module_name=$(basename "$dir" _idl_generated)
            
            # Check Release directory
            if [[ -d "$dir/Release" ]]; then
                for exe in "$dir/Release"/*; do
                    if [[ -x "$exe" && -f "$exe" ]]; then
                        echo -e "${GREEN}[FOUND] $exe${NC}"
                    fi
                done
            fi
            
            # Check Debug directory
            if [[ -d "$dir/Debug" ]]; then
                for exe in "$dir/Debug"/*; do
                    if [[ -x "$exe" && -f "$exe" ]]; then
                        echo -e "${GREEN}[FOUND] $exe${NC}"
                    fi
                done
            fi
            
            # Check root directory
            for exe in "$dir"/*; do
                if [[ -x "$exe" && -f "$exe" && ! -d "$exe" ]]; then
                    echo -e "${GREEN}[FOUND] $exe${NC}"
                fi
            done
        fi
    done
else
    echo -e "${YELLOW}[WARNING] IDL directory not found: $IDL_DIR${NC}"
fi

echo -e "\n${GREEN}Dynamic finder completed successfully!${NC}"