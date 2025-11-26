#!/bin/bash
# Orchestrator: run test_idl_modules.sh, wait until all modules are up, then start run_demo.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
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

SCRIPTS_SH="$PROJECT_ROOT/scripts/sh"
IDL_DIR="$PROJECT_ROOT/IDL"

echo "[INFO] Starting test_idl_modules.sh..."

# Run test script and auto-confirm the final prompt so it doesn't block
( cd "$SCRIPTS_SH" && printf "\n" | bash test_idl_modules.sh ) &

# Build expected process patterns by discovering modules similar to test_idl_modules.sh
declare -a EXPECTED_PATTERNS

mapfile -t GEN_DIRS < <(find "$IDL_DIR" -maxdepth 1 -type d -name "*_idl_generated" | sort)
for d in "${GEN_DIRS[@]}"; do
  mod="$(basename "$d" | sed 's/_idl_generated$//')"
  work_dir="$d"
  if [[ -d "$d/build" ]]; then
    work_dir="$d/build"
  fi
  # pick first *main* executable
  exe=""
  while IFS= read -r -d '' f; do
    if [[ -x "$f" && -f "$f" ]]; then
      exe="$(basename "$f")"
      break
    fi
  done < <(find "$work_dir" -maxdepth 1 -type f -name "*main*" -print0)

  if [[ -n "$exe" ]]; then
    # We expect two processes per module: publisher and subscriber
    EXPECTED_PATTERNS+=("$work_dir/$exe publisher")
    EXPECTED_PATTERNS+=("$work_dir/$exe subscriber")
  fi
done

echo "[INFO] Waiting up to 20s for modules to start (best-effort)..."
deadline=$((SECONDS + 20))
started_any=0
while (( SECONDS <= deadline )); do
  for pat in "${EXPECTED_PATTERNS[@]}"; do
    if pgrep -f -- "$pat" >/dev/null 2>&1; then
      started_any=1
      break
    fi
  done
  if (( started_any == 1 )); then
    echo "[OK] At least one module detected running."
    break
  fi
  sleep 1
done

echo "[INFO] Launching run_demo.sh..."
bash "$PROJECT_ROOT/demo/run_demo/run_demo.sh"
exit_code=$?
echo "[INFO] run_demo.sh exited with code: $exit_code"
exit $exit_code


