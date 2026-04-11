#!/bin/sh
# Integration test: verify home directory and .claude config are accessible.

set -e

if [ ! -d "$HOME" ]; then
  echo "[FAIL]: \$HOME ($HOME) does not exist"
  exit 1
fi

if [ ! -d "$HOME/.claude" ]; then
  echo "[FAIL]: $HOME/.claude does not exist — config volume not mounted?"
  exit 1
fi

if ! touch "$HOME/.claude/.test-write-$$" 2>/dev/null; then
  echo "[FAIL]: $HOME/.claude is not writable"
  exit 1
fi
rm -f "$HOME/.claude/.test-write-$$"

echo "[OK]: home directory and .claude config are accessible and writable"
