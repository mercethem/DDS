#!/bin/bash
# DDS Convenience Aliases - Linux
# This file is dynamically generated - DO NOT EDIT MANUALLY
# Run: bash scripts/sh/setup_environment.sh to regenerate

# Get script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment first
source "$SCRIPT_DIR/export_dds_environment.sh"

# Build aliases
alias dds-build='bash $DDS_SCRIPTS_DIR/build_idl_modules.sh'
alias dds-clean='find $DDS_IDL_DIR -name "*_idl_generated" -type d -exec rm -rf {} + 2>/dev/null || true'
alias dds-env='bash $DDS_SCRIPTS_DIR/setup_environment.sh'

# Security aliases
alias dds-security='cd $DDS_PROJECT_ROOT/scripts/py && python3 apply_security_settings.py'
alias dds-patch-idl='cd $DDS_PROJECT_ROOT/scripts/py && python3 idl_default_data_patcher.py'
alias dds-patch-json='cd $DDS_PROJECT_ROOT/scripts/py && python3 json_reading_patcher.py'

# Demo aliases
alias dds-demo='cd $DDS_PROJECT_ROOT/demo && npm start'

# Quick navigation
alias cd-dds='cd $DDS_PROJECT_ROOT'
alias cd-idl='cd $DDS_IDL_DIR'
alias cd-scripts='cd $DDS_SCRIPTS_DIR'

echo "DDS aliases loaded. Available commands:"
echo "  dds-build     - Build all IDL modules"
echo "  dds-clean     - Clean generated files"
echo "  dds-env       - Refresh environment"
echo "  dds-security  - Apply security patches"
echo "  dds-patch-idl - Patch IDL files"
echo "  dds-patch-json- Patch JSON files"
echo "  dds-demo      - Start demo server"
echo "  cd-dds        - Go to project root"
echo "  cd-idl        - Go to IDL directory"
echo "  cd-scripts    - Go to scripts directory"
