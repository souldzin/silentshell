#!/usr/bin/env bash
# Snapshot test for `silentshell init` with the pi template.
# On first run (no fixture): writes the fixture. On subsequent runs: diffs against it.
#
# Usage:
#   ./tests/test-init-pi.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORK_DIR="$PROJECT_DIR/tmp/test-init-pi"
FIXTURE="$SCRIPT_DIR/test-init-pi.fixture.txt"

# Clean slate
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# Run init with canned inputs:
#   template   -> pi
#   python?    -> y
#   name       -> myproject
#   dockerfile -> (default, accept)
printf "pi\ny\nmyproject\n\n" \
  | PYTHONPATH="$PROJECT_DIR/src" python3 -m silentshell init "$WORK_DIR" > /dev/null

# Build a snapshot: sorted file paths + contents
snapshot() {
  local dir="$1"
  find "$dir" -type f | sort | while IFS= read -r file; do
    echo "=== ${file#"$dir"/} ==="
    cat "$file"
    echo ""
  done
}

ACTUAL="$(snapshot "$WORK_DIR")"

if [[ ! -f "$FIXTURE" ]]; then
  echo "$ACTUAL" > "$FIXTURE"
  echo "[OK] Fixture created: $FIXTURE"
  exit 0
fi

EXPECTED="$(cat "$FIXTURE")"

if [[ "$ACTUAL" == "$EXPECTED" ]]; then
  echo "[OK] test-init-pi"
else
  echo "[FAIL] test-init-pi: snapshot mismatch"
  diff <(echo "$EXPECTED") <(echo "$ACTUAL") || true
  exit 1
fi
