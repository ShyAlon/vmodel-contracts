#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Build a local wheel of this package, without publishing or installing dependencies.
"${PYTHON:-python3.12}" -m pip wheel --no-deps --wheel-dir dist .
