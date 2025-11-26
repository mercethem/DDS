#!/bin/bash
# DDS Project Auto-Setup Script
# This script automatically configures the project when moved to another PC:
# 1. Checks certificates and creates them if missing
# 2. Tests binary executability
# 3. Performs automatic build if needed

set -e

echo "========================================"
echo "DDS Project Auto-Setup"
echo "========================================"
echo
echo "This script prepares the project for use on a new PC."
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$INIT_DIR")"

# Walk up to find project root (contains IDL and scenarios)
CURRENT_DIR="$INIT_DIR"
while [ "$CURRENT_DIR" != "/" ] && [ "$CURRENT_DIR" != "." ]; do
    if [ -d "$CURRENT_DIR/IDL" ] && [ -d "$CURRENT_DIR/scenarios" ]; then
        PROJECT_ROOT="$CURRENT_DIR"
        break
    fi
    CURRENT_DIR="$(dirname "$CURRENT_DIR")"
done

cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo "[INFO] $1"
}

# Step 0: Run run_complete_workflow.sh first (initial setup)
echo "========================================"
echo "STEP 0: Dynamic DDS Workflow (Initial Setup)"
echo "========================================"

if [ ! -f "$PROJECT_ROOT/scripts/sh/run_complete_workflow.sh" ]; then
    print_error "run_complete_workflow.sh not found: $PROJECT_ROOT/scripts/sh/run_complete_workflow.sh"
    exit 1
fi

# Make script executable
chmod +x "$PROJECT_ROOT/scripts/sh/run_complete_workflow.sh"

print_info "Starting Dynamic DDS workflow..."
# Note: run_complete_workflow.sh contains interactive prompts for testing
# If you want non-interactive mode, modify run_complete_workflow.sh or use expect/auto-answer
# run_complete_workflow.sh must be run from scripts/sh directory
(cd "$PROJECT_ROOT/scripts/sh" && bash run_complete_workflow.sh)
if [ $? -eq 0 ]; then
    print_success "Dynamic DDS workflow completed"
else
    print_error "Dynamic DDS workflow failed!"
    exit 1
fi

echo

# Step 1: Check and create certificates
echo "========================================"
echo "STEP 1: Certificate Check"
echo "========================================"

CA_CERT="$PROJECT_ROOT/secure_dds/CA/mainca_cert.pem"
PC_NAME=$(hostname)
PC_CERT_DIR="$PROJECT_ROOT/secure_dds/participants/$PC_NAME"
PC_CERT="$PC_CERT_DIR/${PC_NAME}_cert.pem"

# Certificate check: Check both file existence and date
RECREATE_CERTS=0

if [ ! -f "$CA_CERT" ] || [ ! -f "$PC_CERT" ]; then
    print_warning "Certificates not found or missing. Creating..."
    RECREATE_CERTS=1
else
    # If certificates exist, check their dates
    # Will be renewed every year on January 1st at 00:00 - renew if created before last year's January 1st
    CURRENT_YEAR=$(date +%Y)
    LAST_YEAR=$((CURRENT_YEAR - 1))
    LAST_YEAR_JAN1=$(date -d "${LAST_YEAR}-01-01 00:00:00" +%s 2>/dev/null)
    if [ -z "$LAST_YEAR_JAN1" ] || [ "$LAST_YEAR_JAN1" -eq 0 ]; then
        # Alternative for macOS or different date command
        LAST_YEAR_JAN1=$(date -j -f "%Y-%m-%d %H:%M:%S" "${LAST_YEAR}-01-01 00:00:00" +%s 2>/dev/null || echo 0)
    fi
    CA_MTIME=$(stat -c %Y "$CA_CERT" 2>/dev/null || stat -f %m "$CA_CERT" 2>/dev/null || echo 0)
    
    # If date calculation failed, use old check (1 year)
    if [ "$LAST_YEAR_JAN1" -eq 0 ] || [ "$CA_MTIME" -eq 0 ]; then
        CA_AGE=$(( $(date +%s) - $CA_MTIME ))
        if [ $CA_AGE -gt 31536000 ] || [ $CA_AGE -lt 0 ]; then
            print_warning "Certificates appear old or system time is incorrect. Recreating..."
            RECREATE_CERTS=1
        else
            print_success "Certificates exist"
        fi
    # Renew if CA certificate was created before last year's January 1st or system time is incorrect
    elif [ $CA_MTIME -lt $LAST_YEAR_JAN1 ] || [ $CA_MTIME -lt 0 ]; then
        print_warning "Certificates were created before last year's January 1st or system time is incorrect. Recreating..."
        RECREATE_CERTS=1
    else
        print_success "Certificates exist (created this year or after last year's January 1st)"
    fi
fi

if [ $RECREATE_CERTS -eq 1 ]; then
    # Check if Python scripts exist
    if [ ! -f "scripts/py/generate_security_certificates.py" ]; then
        print_error "generate_security_certificates.py not found!"
        exit 1
    fi
    
    # Run certificate generation
    if python3 scripts/py/generate_security_certificates.py; then
        print_success "Certificates created"
    else
        print_error "Certificate creation failed!"
        exit 1
    fi
fi

echo

# Step 2a: Clean duplicate dynamic code blocks (if any)
echo "========================================"
echo "STEP 2a: Cleaning Duplicate Code Blocks"
echo "========================================"

if [ -f "scripts/py/clean_duplicate_code.py" ]; then
    if python3 scripts/py/clean_duplicate_code.py > /dev/null 2>&1; then
        print_success "Duplicate code blocks cleaned"
    else
        print_warning "Cleanup script executed (result pending)"
    fi
else
    print_warning "clean_duplicate_code.py not found (skipping...)"
fi

echo

# Step 2b: Fix CMake portability (hardcoded paths, RPATH, etc.)
echo "========================================"
echo "STEP 2b: CMake Portability Fix"
echo "========================================"

if [ -f "scripts/py/fix_cmake_rpath.py" ]; then
    if python3 scripts/py/fix_cmake_rpath.py > /dev/null 2>&1; then
        print_success "CMake files made portable"
    else
        print_warning "CMake fix executed (result pending)"
    fi
else
    print_warning "fix_cmake_rpath.py not found (skipping...)"
fi

echo

# Step 2: Apply security patches (if needed)
echo "========================================"
echo "STEP 2: Security Configuration"
echo "========================================"

if [ -f "scripts/py/apply_security_settings.py" ]; then
    if python3 scripts/py/apply_security_settings.py > /dev/null 2>&1; then
        print_success "Security settings checked"
    else
        print_warning "Warning occurred while applying security settings (continuing...)"
    fi
else
    print_warning "apply_security_settings.py not found (skipping...)"
fi

echo

# Step 3: Check if binaries exist and are executable
echo "========================================"
echo "STEP 3: Binary Check"
echo "========================================"

NEED_BUILD=0
BINARY_COUNT=0
MISSING_BINARIES=()

# Check for main executables in each IDL module
for idl_dir in "$PROJECT_ROOT/IDL"/*_idl_generated; do
    if [ -d "$idl_dir" ]; then
        MODULE_NAME=$(basename "$idl_dir" | sed 's/_idl_generated//')
        MAIN_BINARY="$idl_dir/build/${MODULE_NAME}main"
        
        # Try build/ first, then root
        if [ ! -f "$MAIN_BINARY" ]; then
            MAIN_BINARY="$idl_dir/${MODULE_NAME}main"
        fi
        
        BINARY_COUNT=$((BINARY_COUNT + 1))
        
        if [ -f "$MAIN_BINARY" ] && [ -x "$MAIN_BINARY" ]; then
            # Test if binary can actually run (check for segfault or library errors)
            if "$MAIN_BINARY" --help > /dev/null 2>&1 || timeout 1 "$MAIN_BINARY" > /dev/null 2>&1; then
                print_success "$MODULE_NAME binary is working"
            else
                print_warning "$MODULE_NAME binary is not working (may be a library error)"
                NEED_BUILD=1
                MISSING_BINARIES+=("$MODULE_NAME")
            fi
        else
            print_warning "$MODULE_NAME binary not found or cannot be executed"
            NEED_BUILD=1
            MISSING_BINARIES+=("$MODULE_NAME")
        fi
    fi
done

echo

# Step 4: Build if needed
if [ $NEED_BUILD -eq 1 ]; then
    echo "========================================"
    echo "STEP 4: Building Missing Binaries"
    echo "========================================"
    
    print_info "Starting build for missing or non-working binaries..."
    
    if [ ! -f "scripts/sh/build_idl_modules.sh" ]; then
        print_error "build_idl_modules.sh not found!"
        exit 1
    fi
    
    # Make script executable
    chmod +x scripts/sh/build_idl_modules.sh
    
    # Run builder
    if bash scripts/sh/build_idl_modules.sh; then
        print_success "Build completed"
    else
        print_error "Build failed!"
        echo
        print_warning "To build manually:"
        echo "  scripts/sh/build_idl_modules.sh"
        exit 1
    fi
else
    echo "========================================"
    echo "STEP 4: Build Check"
    echo "========================================"
    print_success "All binaries exist and are working - build not needed"
fi

echo

# Step 5: Verify and fix participant certificate compatibility with CA
echo "========================================"
echo "STEP 5: Participant Certificate Verification"
echo "========================================"

CA_CERT="$PROJECT_ROOT/secure_dds/CA/mainca_cert.pem"
CA_KEY="$PROJECT_ROOT/secure_dds/CA/private/mainca_key.pem"
PARTICIPANT_DIR="$PROJECT_ROOT/secure_dds/participants/$PC_NAME"
PARTICIPANT_CERT="$PARTICIPANT_DIR/${PC_NAME}_cert.pem"
PARTICIPANT_KEY="$PARTICIPANT_DIR/${PC_NAME}_key.pem"
PARTICIPANT_CSR="$PARTICIPANT_DIR/${PC_NAME}.csr"
APP_CONF="$PROJECT_ROOT/secure_dds/appconf.cnf"

# Check if CA exists
if [ ! -f "$CA_CERT" ]; then
    print_error "CA certificate not found: $CA_CERT"
    print_warning "Participant certificate cannot be verified (skipping...)"
else
    # Verify current participant cert against CA
    if [ -f "$PARTICIPANT_CERT" ]; then
        if openssl verify -CAfile "$CA_CERT" "$PARTICIPANT_CERT" > /dev/null 2>&1; then
            print_success "Participant certificate is compatible with CA"
        else
            print_warning "Participant certificate does not match CA!"
            print_info "Recreating participant certificate..."
            
            # Check CA key exists
            if [ ! -f "$CA_KEY" ]; then
                print_error "CA private key not found: $CA_KEY"
                print_warning "Participant certificate cannot be recreated (skipping...)"
            else
                # Backup old certificate if exists
                if [ -f "$PARTICIPANT_CERT" ]; then
                    mv "$PARTICIPANT_CERT" "${PARTICIPANT_CERT}.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
                fi
                
                # Keep the private key, we'll regenerate the certificate
                if [ ! -f "$PARTICIPANT_KEY" ]; then
                    print_warning "Private key not found, creating..."
                    mkdir -p "$PARTICIPANT_DIR"
                    openssl genrsa -out "$PARTICIPANT_KEY" 4096 > /dev/null 2>&1
                fi
                
                # Create CSR
                if [ ! -f "$APP_CONF" ]; then
                    print_error "appconf.cnf not found: $APP_CONF"
                    print_warning "CSR cannot be created (skipping...)"
                else
                    openssl req -new -key "$PARTICIPANT_KEY" \
                        -out "$PARTICIPANT_CSR" \
                        -config "$APP_CONF" \
                        -subj "/C=TR/ST=Istanbul/L=Istanbul/O=DDS Security System/OU=Military Applications/CN=${PC_NAME}_Participant/emailAddress=${PC_NAME,,}@dds-security.local" \
                        > /dev/null 2>&1
                    
                    # Sign certificate with CA
                    if openssl x509 -req -in "$PARTICIPANT_CSR" \
                        -CA "$CA_CERT" \
                        -CAkey "$CA_KEY" \
                        -CAcreateserial \
                        -out "$PARTICIPANT_CERT" \
                        -days 99999 \
                        -sha256 \
                        -extensions v3_req \
                        -extfile "$APP_CONF" \
                        > /dev/null 2>&1; then
                        
                        # Verify the new certificate
                        if openssl verify -CAfile "$CA_CERT" "$PARTICIPANT_CERT" > /dev/null 2>&1; then
                            print_success "Participant certificate recreated and verified with new CA"
                        else
                            print_warning "Participant certificate created but verification failed"
                        fi
                    else
                        print_error "Participant certificate could not be created"
                    fi
                fi
            fi
        fi
    else
        print_warning "Participant certificate not found: $PARTICIPANT_CERT"
        print_info "generate_security_certificates.py should be run in STEP 1 to create certificate"
    fi
fi

echo

# Step 6: Build monitoring application
echo "========================================"
echo "STEP 6: Building Monitoring Application"
echo "========================================"

MONITORING_BUILD_SCRIPT="$PROJECT_ROOT/monitoring/build_monitoring/build_monitoring.sh"

if [ -f "$MONITORING_BUILD_SCRIPT" ]; then
    print_info "Building monitoring application..."
    
    # Make script executable
    chmod +x "$MONITORING_BUILD_SCRIPT"
    
    # Run monitoring build script
    if bash "$MONITORING_BUILD_SCRIPT"; then
        print_success "Monitoring application built successfully"
    else
        print_warning "Monitoring build failed (continuing anyway...)"
    fi
else
    print_warning "build_monitoring.sh not found at: $MONITORING_BUILD_SCRIPT (skipping...)"
fi

echo
echo "========================================"
echo "Setup Completed!"
echo "========================================"
echo
print_success "Project is ready to use!"
echo
echo "Usage:"
echo "  Publisher:   IDL/<MODULE>_idl_generated/build/<MODULE>main publisher"
echo "  Subscriber: IDL/<MODULE>_idl_generated/build/<MODULE>main subscriber"
echo
echo "Example:"
echo "  IDL/Messaging_idl_generated/build/Messagingmain publisher"
echo

exit 0
