#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# CI runs Python 3.12. Any 3.12 or newer works locally.
MIN_MINOR=12

py_version() {  # prints "MAJOR.MINOR" for the given interpreter, or nothing if it cannot run
  "$1" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true
}

py_ok() {  # true when the interpreter is Python 3.$MIN_MINOR or newer
  local v
  v="$(py_version "$1")"
  [[ "$v" =~ ^3\.([0-9]+)$ ]] && (( BASH_REMATCH[1] >= MIN_MINOR ))
}

if [[ -x .venv/bin/python ]]; then
  if ! py_ok .venv/bin/python; then
    found="$(py_version .venv/bin/python)"
    echo "The existing .venv uses Python ${found:-that cannot run}; this script needs Python 3.${MIN_MINOR} or newer." >&2
    echo "Fix: rm -rf .venv   (then run this script again; it will build a new one)" >&2
    exit 1
  fi
else
  chosen=""
  if [[ -n "${PYTHON:-}" ]]; then
    if ! py_ok "$PYTHON"; then
      echo "PYTHON=$PYTHON is not Python 3.${MIN_MINOR} or newer (it reports: $(py_version "$PYTHON")). Point it at python3.12 or newer." >&2
      exit 1
    fi
    chosen="$PYTHON"
  else
    for candidate in python3.12 python3.13 python3.14 python3; do
      if command -v "$candidate" >/dev/null 2>&1 && py_ok "$candidate"; then chosen="$candidate"; break; fi
    done
  fi
  if [[ -z "$chosen" ]]; then
    echo "No Python 3.${MIN_MINOR} or newer found on PATH." >&2
    echo "Install one (macOS: brew install python@3.12), or point at one: PYTHON=/path/to/python3.12 $0" >&2
    exit 1
  fi
  "$chosen" -m venv .venv
fi
PYTHON=.venv/bin/python
"$PYTHON" -m pip install -e '.[dev]'
"$PYTHON" -m pytest -q
