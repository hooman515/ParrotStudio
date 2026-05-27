#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_PACKAGE="$ROOT/frontend/macos/ParrotStudioApp"
APP_ICON="$APP_PACKAGE/Resources/AppIcon.icns"
DIST="${PARROT_DIST:-/Applications}"
APP="$DIST/Parrot Studio.app"
CONTENTS="$APP/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"
EXECUTABLE="$MACOS/ParrotStudio"
PYTHON_LIB="$RESOURCES/python_lib"

MODE="${1:-}"
SIGN_IDENTITY="${PARROT_SIGN_IDENTITY:-}"

pkill -x ParrotStudio >/dev/null 2>&1 || true
sleep 0.3
pkill -f '[p]arrot_studio.main' >/dev/null 2>&1 || true

swift build --package-path "$APP_PACKAGE"
BUILT="$APP_PACKAGE/.build/debug/ParrotStudio"

rm -rf "$APP"
mkdir -p "$MACOS" "$RESOURCES"
cp "$BUILT" "$EXECUTABLE"
chmod +x "$EXECUTABLE"
cp -R "$ROOT/backend" "$RESOURCES/backend"
if [[ -f "$APP_ICON" ]]; then
  cp "$APP_ICON" "$RESOURCES/AppIcon.icns"
fi

if [[ "${PARROT_SKIP_VENDOR_DEPS:-0}" != "1" ]]; then
  DEPS_PYTHON="${PARROT_DEPS_PYTHON:-$(command -v python3)}"
  "$DEPS_PYTHON" -m pip install \
    --quiet \
    --disable-pip-version-check \
    --target "$PYTHON_LIB" \
    websockets 'httpx>=0.27'
fi

cat > "$CONTENTS/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key><string>en</string>
  <key>CFBundleExecutable</key><string>ParrotStudio</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundleIdentifier</key><string>com.parrot.studio</string>
  <key>CFBundleName</key><string>Parrot Studio</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>0.1.0</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>LSMinimumSystemVersion</key><string>26.0</string>
  <key>NSHumanReadableCopyright</key><string>Copyright © 2026</string>
  <key>NSPrincipalClass</key><string>NSApplication</string>
</dict>
</plist>
PLIST

/usr/bin/xattr -dr com.apple.provenance "$APP" 2>/dev/null || true
/usr/bin/xattr -cr "$APP" 2>/dev/null || true
find "$APP" -exec /usr/bin/xattr -c {} + 2>/dev/null || true
if [[ -z "$SIGN_IDENTITY" ]]; then
  SIGN_IDENTITY="$(security find-identity -v -p codesigning 2>/dev/null | sed -n 's/.*"\(Apple Development:[^"]*\)".*/\1/p' | head -1)"
fi
if [[ -z "$SIGN_IDENTITY" ]]; then
  SIGN_IDENTITY="-"
fi
/usr/bin/codesign --force --deep --sign "$SIGN_IDENTITY" --identifier com.parrot.studio "$APP"

case "$MODE" in
  --verify)
    /usr/bin/open -n "$APP"
    sleep 2
    pgrep -x ParrotStudio >/dev/null
    echo "Parrot Studio launched."
    ;;
  --logs)
    /usr/bin/open -n "$APP"
    /usr/bin/log stream --info --predicate 'process == "ParrotStudio"'
    ;;
  --telemetry)
    /usr/bin/open -n "$APP"
    /usr/bin/log stream --info --predicate 'subsystem BEGINSWITH "com.parrot.studio"'
    ;;
  --debug)
    lldb "$EXECUTABLE"
    ;;
  "")
    /usr/bin/open -n "$APP"
    ;;
  *)
    echo "Unknown option: $MODE" >&2
    exit 2
    ;;
esac
