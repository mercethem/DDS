#!/bin/bash
# DDS Convenience Aliases - Linux
# This file is dynamically generated - DO NOT EDIT MANUALLY
# Run: bash scripts/sh/dynamic_environment_setup.sh to regenerate

# Get script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment first
source "$SCRIPT_DIR/dds_environment_linux.sh"

# Build aliases
alias dds-build='bash $DDS_SCRIPTS_DIR/sh/IDL_BUILDER.sh'
alias dds-clean='find $DDS_IDL_DIR -name "*_idl_generated" -type d -exec rm -rf {} + 2>/dev/null || true'
alias dds-env='bash $DDS_SCRIPTS_DIR/sh/dynamic_environment_setup.sh'

# Security aliases
alias dds-security='cd $DDS_SCRIPTS_DIR/../py && python3 security.py'
alias dds-patch-idl='cd $DDS_SCRIPTS_DIR/../py && python3 idl_patcher.py'
alias dds-patch-json='cd $DDS_SCRIPTS_DIR/../py && python3 json_patcher.py'

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
