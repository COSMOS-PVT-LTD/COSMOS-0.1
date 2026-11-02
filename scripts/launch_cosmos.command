#!/bin/bash
# Double-click launcher for COSMOS 0.1 native desktop (macOS).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COSMOS_DESKTOP_APP="$HOME/Applications/COSMOS Desktop.app"
if [ -x "$COSMOS_DESKTOP_APP/Contents/MacOS/cosmos-launcher" ]; then
  exec /usr/bin/open "$COSMOS_DESKTOP_APP"
fi
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
