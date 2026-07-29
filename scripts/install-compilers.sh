#!/usr/bin/env bash
# Wrapper → code/scripts/install-compilers.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "${ROOT}/code/scripts/install-compilers.sh" "$@"
