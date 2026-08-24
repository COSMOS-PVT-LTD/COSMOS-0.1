#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
PY="${PYTHON:-python3}"

if ! "$PY" -c "import webview" >/dev/null 2>&1; then
  echo "COSMOS desktop runtime not installed. Running installer..."
  bash "$ROOT/scripts/install_desktop_deps.sh"
fi

exec "$PY" main.py "$@"
