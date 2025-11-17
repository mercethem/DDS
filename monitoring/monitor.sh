#!/usr/bin/env bash
set -euo pipefail

# Always run from this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BUILD_BIN="$SCRIPT_DIR/build/monitor"

echo "[monitor.sh] Building monitor (if needed)..."
if [[ ! -x "$BUILD_BIN" ]]; then
  chmod +x "$SCRIPT_DIR/build.sh" 2>/dev/null || true
  "$SCRIPT_DIR/build.sh"
else
  # Try a fast rebuild to ensure it's up to date
  chmod +x "$SCRIPT_DIR/build.sh" 2>/dev/null || true
  "$SCRIPT_DIR/build.sh" >/dev/null || true
fi

if [[ ! -x "$BUILD_BIN" ]]; then
  echo "[monitor.sh] ERROR: build/monitor not found."
  exit 1
fi

echo "[monitor.sh] Running: $BUILD_BIN"
# Pass MONITOR_DOMAINS as CLI arg if set
if [[ -n "${MONITOR_DOMAINS-}" ]]; then
  echo "[monitor.sh] MONITOR_DOMAINS=$MONITOR_DOMAINS"
  exec "$BUILD_BIN" "$MONITOR_DOMAINS"
else
  exec "$BUILD_BIN"
fi


