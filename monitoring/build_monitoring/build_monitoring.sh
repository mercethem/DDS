#!/usr/bin/env bash
set -euo pipefail

# Resolve script and build directories
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MONITORING_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$MONITORING_DIR/build"

echo "[build_monitoring.sh] Script dir: $SCRIPT_DIR"
echo "[build_monitoring.sh] Monitoring dir: $MONITORING_DIR"
echo "[build_monitoring.sh] Build dir:  $BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Ensure compilers are available
if ! command -v cmake >/dev/null 2>&1; then
  echo "[build_monitoring.sh] ERROR: cmake not found. Install cmake and retry." >&2
  exit 1
fi

# Try to help CMake find Fast-DDS and Fast-CDR
# Common install locations: /usr/local, /opt/fastdds
PREFIX_CANDIDATES=("/usr/local" "/opt/fastdds")

# Extend LD_LIBRARY_PATH for runtime linkage
for P in "${PREFIX_CANDIDATES[@]}"; do
  if [[ -d "$P/lib" ]]; then
    export LD_LIBRARY_PATH="$P/lib:${LD_LIBRARY_PATH-}"
  fi
done

# Build a CMAKE_PREFIX_PATH including any existing value
CPPATH="${CMAKE_PREFIX_PATH-}"
for P in "${PREFIX_CANDIDATES[@]}"; do
  if [[ -d "$P/lib/cmake" || -d "$P/share/cmake" || -d "$P" ]]; then
    if [[ -n "$CPPATH" ]]; then
      CPPATH="$CPPATH;$P"
    else
      CPPATH="$P"
    fi
  fi
done
export CMAKE_PREFIX_PATH="$CPPATH"

echo "[monitor/build_monitoring] CMAKE_PREFIX_PATH=$CMAKE_PREFIX_PATH"
echo "[monitor/build_monitoring] LD_LIBRARY_PATH=$LD_LIBRARY_PATH"

# Configure
echo "[monitor/build_monitoring] Configuring with CMake..."
cmake -S "$MONITORING_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release

# Build with available cores
JOBS=$(command -v nproc >/dev/null 2>&1 && nproc || echo 4)
echo "[monitor/build_monitoring] Building with -j$JOBS..."
cmake --build "$BUILD_DIR" -j"$JOBS"

if [[ -x "$BUILD_DIR/monitor" ]]; then
  echo "[monitor/build_monitoring] Built monitor at: $BUILD_DIR/monitor"
else
  echo "[monitor/build_monitoring] ERROR: build finished but monitor binary not found." >&2
  exit 2
fi
