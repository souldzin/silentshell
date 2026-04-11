#!/usr/bin/env bash
# Integration test: starts a silentshell container for THIS project
# (via silentshell.sh) and runs the agent test suite inside it.
#
# This goes through the full silentshell.sh code path, so it
# tests the actual container setup — mounts, ignore-paths, user, etc.
#
# Usage:
#   ./tests/test-environment.sh          # uses existing image
#   ./tests/test-environment.sh --build  # rebuilds image first

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Options ---------------------------------------------------------------
BUILD_ARG=""
if [[ "${1:-}" == "--build" ]]; then
  BUILD_ARG="--build"
fi

# --- Setup local env before starting environment -----------------------------
# NOTE: We want to test the behavior of .test-ignore-paths so let's write to
# it from this environment and then assert it is empty in the otherworld.
rm -rf ${PROJECT_DIR}/tmp/.test-ignore-paths
mkdir -p ${PROJECT_DIR}/tmp/.test-ignore-paths
echo "Hello World" >${PROJECT_DIR}/tmp/.test-ignore-paths/hello.md

# --- Run tests via silentshell.sh --------------------------------------------
echo "* Running environment integration tests..."

TEST_CMD='for t in /project/tests/environment/test-*.sh; do echo "--- $t ---"; sh "$t"; done'

OUTPUT=$("$PROJECT_DIR/silentshell.sh" start $BUILD_ARG --no-interactive --exec "$TEST_CMD" "$PROJECT_DIR" 2>&1) || true

echo "$OUTPUT"

# --- Check results ---------------------------------------------------------
TOTAL=$(echo "$OUTPUT" | grep -c "\[OK\]\|\[FAIL\]" || true)
PASSED=$(echo "$OUTPUT" | grep -c "\[OK\]" || true)
FAILED=$(echo "$OUTPUT" | grep -c "\[FAIL\]" || true)

echo ""
echo "--- Results: $PASSED/$TOTAL passed ---"

if [[ "$FAILED" -gt 0 ]]; then
  echo "[FAIL] Integration tests FAILED"
  exit 1
fi

if [[ "$PASSED" -eq 0 ]]; then
  echo "[FAIL] No tests ran"
  exit 1
fi

echo "[OK] All integration tests passed"
