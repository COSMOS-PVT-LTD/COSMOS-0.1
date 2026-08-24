#!/usr/bin/env bash
# Install COSMOS native desktop dependencies (pywebview).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
echo "Installing COSMOS desktop shell dependencies..."
"$PY" -m pip install -r requirements-desktop.txt
echo ""
echo "Verify native runtime:"
"$PY" -c "import webview; print('pywebview OK')"
echo ""
echo "Launch COSMOS as a native application:"
echo "  $PY main.py"
