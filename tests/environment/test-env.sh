#!/bin/sh
# Integration test: verify that env variables defined in .silentshell.toml are
# loaded into the container.

set -e

EXPECTED_VALUE="lorem-ipsum"
ACTUAL_VALUE="${SILENTSHELL_TEST_ENV}"

if [ "${ACTUAL_VALUE}" = "${EXPECTED_VALUE}" ]; then
  echo "[OK]: Writing environment variables work"
  exit 0
else
  echo "[FAIL]: Expected SILENTSHELL_TEST_ENV to be ${EXPECTED_VALUE} (found: ${ACTUAL_VALUE})"
  exit 1
fi
