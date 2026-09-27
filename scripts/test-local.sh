#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Use Python 3.12 on the local machine to match Actions.
if [[ ! -x .venv/bin/python ]]; then
  "${PYTHON:-python3.12}" -m venv .venv
fi
PYTHON=.venv/bin/python
if [[ "$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" != "3.12" ]]; then
  echo "Expected Python 3.12 in .venv; remove or rename .venv and retry" >&2
  exit 1
fi
"$PYTHON" -m pip install -e '.[dev]'
"$PYTHON" -m pytest -q
