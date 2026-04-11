#!/bin/sh
# Integration test: verify tmpfs mounts for ignore-paths allow execution.
# .test-ignore-paths must be listed in .silentshell.toml ignore-paths.

set -e

MOUNT_OPTS=$(mount | grep "/project/tmp/.test-ignore-paths" || true)

if [ -z "$MOUNT_OPTS" ]; then
  echo "[FAIL]: /project/.test-ignore-paths is not a tmpfs mount"
  exit 1
fi

if echo "$MOUNT_OPTS" | grep -q "noexec"; then
  echo "[FAIL]: tmpfs mount has noexec — binaries in ignored paths won't run"
  echo "  $MOUNT_OPTS"
  exit 1
fi

if [ -n "$(ls -A /project/tmp/.test-ignore-paths 2>/dev/null)" ]; then
  echo "[FAIL]: tmpfs mount is not empty — unexpected files present"
  ls -A /project/tmp/.test-ignore-paths
  exit 1
fi

echo "[OK]: tmpfs mount allows exec and is empty"
