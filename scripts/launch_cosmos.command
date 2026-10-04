#!/bin/bash
# Double-click launcher for COSMOS 0.1 native desktop (macOS).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ -x "$ROOT/.venv-remediation/bin/python" ]; then
  PY="${PYTHON:-$ROOT/.venv-remediation/bin/python}"
else
  PY="${PYTHON:-python3}"
fi

if ! "$PY" -c "import webview" 2>/dev/null; then
  osascript -e 'display dialog "COSMOS desktop dependencies are not installed.\n\nRun in Terminal:\ncd '"$ROOT"'\npip install -r requirements-desktop.txt" buttons {"OK"} default button "OK" with title "COSMOS 0.1"'
  exit 1
fi

exec "$PY" main.py
