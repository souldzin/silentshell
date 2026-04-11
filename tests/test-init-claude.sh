#!/usr/bin/env bash
# Snapshot test for `silentshell init` with the claude template.
# On first run (no fixture): writes the fixture. On subsequent runs: diffs against it.
#
# Usage:
#   ./tests/test-init-claude.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORK_DIR="$PROJECT_DIR/tmp/test-init-claude"
FIXTURE="$SCRIPT_DIR/test-init-claude.fixture.txt"

# Clean slate
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# Run init with canned inputs:
#   template   -> claude
#   python?    -> n
#   name       -> myproject
#   dockerfile -> (default, accept)
printf "claude\nn\nmyproject\n\n" |
  PYTHONPATH="$PROJECT_DIR/src" python3 -m silentshell init "$WORK_DIR" >/dev/null

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
  echo "$ACTUAL" >"$FIXTURE"
  echo "[OK] Fixture created: $FIXTURE"
  exit 0
fi

EXPECTED="$(cat "$FIXTURE")"

if [[ "$ACTUAL" == "$EXPECTED" ]]; then
  echo "[OK] test-init-claude"
else
  echo "[FAIL] test-init-claude: snapshot mismatch"
  diff <(echo "$EXPECTED") <(echo "$ACTUAL") || true
  exit 1
fi
