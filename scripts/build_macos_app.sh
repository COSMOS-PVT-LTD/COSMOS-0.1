#!/usr/bin/env bash
# Build a double-clickable macOS application bundle: dist/COSMOS 0.1.app
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
APP_NAME="COSMOS 0.1"
APP_DIR="$ROOT/dist/${APP_NAME}.app"
PY="${PYTHON:-python3}"
ICON_SRC="$ROOT/gui/assets/cosmos_logo.png"

mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources"

cat > "$APP_DIR/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>cosmos-launcher</string>
  <key>CFBundleIconFile</key>
  <string>cosmos_logo</string>
  <key>CFBundleIdentifier</key>
  <string>com.cosmos.engineering.cosmos-0-1</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>COSMOS 0.1</string>
  <key>CFBundleDisplayName</key>
  <string>COSMOS 0.1</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.1.0</string>
  <key>CFBundleVersion</key>
  <string>0.1.0</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>LSUIElement</key>
  <false/>
</dict>
</plist>
PLIST

cat > "$APP_DIR/Contents/MacOS/cosmos-launcher" <<LAUNCHER
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$ROOT"
export PYTHONPATH="\$REPO_ROOT\${PYTHONPATH:+:\$PYTHONPATH}"
PY="$PY"
if ! "\$PY" -c "import webview" >/dev/null 2>&1; then
  osascript -e 'display alert "COSMOS 0.1" message "Desktop runtime missing. Run scripts/install_desktop_deps.sh first." as critical'
  exit 1
fi
cd "\$REPO_ROOT"
exec "\$PY" "\$REPO_ROOT/main.py"
LAUNCHER

chmod +x "$APP_DIR/Contents/MacOS/cosmos-launcher"

if [[ -f "$ICON_SRC" ]]; then
  cp "$ICON_SRC" "$APP_DIR/Contents/Resources/cosmos_logo.png"
  if command -v sips >/dev/null 2>&1; then
    mkdir -p "$APP_DIR/Contents/Resources/cosmos_logo.iconset"
    sips -z 16 16 "$ICON_SRC" --out "$APP_DIR/Contents/Resources/cosmos_logo.iconset/icon_16x16.png" >/dev/null
    sips -z 32 32 "$ICON_SRC" --out "$APP_DIR/Contents/Resources/cosmos_logo.iconset/icon_16x16@2x.png" >/dev/null
    sips -z 32 32 "$ICON_SRC" --out "$APP_DIR/Contents/Resources/cosmos_logo.iconset/icon_32x32.png" >/dev/null
    sips -z 64 64 "$ICON_SRC" --out "$APP_DIR/Contents/Resources/cosmos_logo.iconset/icon_32x32@2x.png" >/dev/null
    sips -z 128 128 "$ICON_SRC" --out "$APP_DIR/Contents/Resources/cosmos_logo.iconset/icon_128x128.png" >/dev/null
    sips -z 256 256 "$ICON_SRC" --out "$APP_DIR/Contents/Resources/cosmos_logo.iconset/icon_128x128@2x.png" >/dev/null
    sips -z 256 256 "$ICON_SRC" --out "$APP_DIR/Contents/Resources/cosmos_logo.iconset/icon_256x256.png" >/dev/null
    sips -z 512 512 "$ICON_SRC" --out "$APP_DIR/Contents/Resources/cosmos_logo.iconset/icon_256x256@2x.png" >/dev/null
    sips -z 512 512 "$ICON_SRC" --out "$APP_DIR/Contents/Resources/cosmos_logo.iconset/icon_512x512.png" >/dev/null
    sips -z 1024 1024 "$ICON_SRC" --out "$APP_DIR/Contents/Resources/cosmos_logo.iconset/icon_512x512@2x.png" >/dev/null
    iconutil -c icns "$APP_DIR/Contents/Resources/cosmos_logo.iconset" -o "$APP_DIR/Contents/Resources/cosmos_logo.icns" || true
    rm -rf "$APP_DIR/Contents/Resources/cosmos_logo.iconset"
  fi
fi

echo "Built: $APP_DIR"
echo "Double-click '${APP_NAME}.app' in Finder to launch COSMOS as a native application."
