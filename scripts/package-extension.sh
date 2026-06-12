#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/dist"

rm -rf "$OUT/extension"
mkdir -p "$OUT/extension"
cp "$ROOT/extension/manifest.json" "$OUT/extension/"
cp "$ROOT/extension/background.js" "$ROOT/extension/content.js" "$OUT/extension/"
cp "$ROOT/extension/popup.html" "$ROOT/extension/popup.css" "$ROOT/extension/popup.js" \
  "$OUT/extension/"
cp "$ROOT/extension/options.html" "$ROOT/extension/options.css" "$ROOT/extension/options.js" \
  "$OUT/extension/"
cp -R "$ROOT/extension/assets" "$ROOT/extension/lib" "$OUT/extension/"

cd "$OUT/extension"
rm -f "$OUT/visionx-extension.zip"
zip -qr "$OUT/visionx-extension.zip" .
echo "$OUT/visionx-extension.zip"
