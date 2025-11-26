#!/usr/bin/env bash
set -euo pipefail

# Always run from this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$(dirname "$SCRIPT_DIR")"
cd "$MONITORING_DIR"

BUILD_BIN="$MONITORING_DIR/build/monitor"

echo "[run_monitoring.sh] Building monitor (if needed)..."
if [[ ! -x "$BUILD_BIN" ]]; then
  chmod +x "$MONITORING_DIR/build_monitoring/build_monitoring.sh" 2>/dev/null || true
  "$MONITORING_DIR/build_monitoring/build_monitoring.sh"
else
  # Try a fast rebuild to ensure it's up to date
  chmod +x "$MONITORING_DIR/build_monitoring/build_monitoring.sh" 2>/dev/null || true
  "$MONITORING_DIR/build_monitoring/build_monitoring.sh" >/dev/null || true
fi

if [[ ! -x "$BUILD_BIN" ]]; then
  echo "[run_monitoring.sh] ERROR: build/monitor not found."
  exit 1
fi

echo "[run_monitoring.sh] Running: $BUILD_BIN"
# Pass MONITOR_DOMAINS as CLI arg if set
if [[ -n "${MONITOR_DOMAINS-}" ]]; then
  echo "[run_monitoring.sh] MONITOR_DOMAINS=$MONITOR_DOMAINS"
  exec "$BUILD_BIN" "$MONITOR_DOMAINS"
else
  exec "$BUILD_BIN"
fi


