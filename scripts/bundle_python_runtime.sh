#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/Parrot Studio.app" >&2
  exit 2
fi

APP_BUNDLE="$1"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESOURCES="$APP_BUNDLE/Contents/Resources"
RUNTIME="$RESOURCES/python"

find_python312() {
  if [[ -n "${PYTHON_3_12:-}" && -x "$PYTHON_3_12" ]]; then
    echo "$PYTHON_3_12"
    return 0
  fi
  if command -v python3.12 >/dev/null 2>&1; then
    command -v python3.12
    return 0
  fi
  if command -v uv >/dev/null 2>&1; then
    uv python find 3.12 2>/dev/null && return 0
  fi
  return 1
}

PY312="$(find_python312 || true)"
if [[ -z "$PY312" ]]; then
  cat >&2 <<'EOF'
Could not find CPython 3.12.

Install or point to Python 3.12, then rerun:
  PYTHON_3_12=/path/to/python3.12 scripts/bundle_python_runtime.sh '/Applications/Parrot Studio.app'

If you use uv:
  uv python install 3.12
EOF
  exit 1
fi

rm -rf "$RUNTIME"
mkdir -p "$RESOURCES"
"$PY312" -m venv "$RUNTIME"
"$RUNTIME/bin/python" -m pip install --upgrade pip
"$RUNTIME/bin/python" -m pip install "$ROOT"

echo "Bundled Python runtime at $RUNTIME"
