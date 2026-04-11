#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

${SCRIPT_DIR}/test-init-claude.sh
${SCRIPT_DIR}/test-init-pi.sh
${SCRIPT_DIR}/test-environment.sh
