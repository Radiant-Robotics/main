#!/bin/bash
# Rebuild the logo SVGs, PNG exports, favicons, and social image.
#
# Usage: brand/tools/export.sh path/to/Inter-Bold.ttf
# Needs: python3 with fonttools + uharfbuzz, Google Chrome, ImageMagick.
set -euo pipefail

FONT="$1"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOGO="$ROOT/brand/logo"
TMP="$(mktemp -d)"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PY="${PYTHON:-python3}"

"$PY" "$ROOT/brand/tools/build_logos.py" "$FONT" "$ROOT/brand"

# Screenshot a local HTML file at an exact size, with a transparent background.
shoot() { # html out width height
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
    --default-background-color=00000000 --force-device-scale-factor=1 \
    --virtual-time-budget=5000 --window-size="$3,$4" --screenshot="$2" "file://$1" >/dev/null 2>&1
}

render_svg() { # svg out width height
  printf '<html><body style="margin:0"><img src="file://%s" style="display:block;width:%spx;height:%spx"></body></html>' \
    "$1" "$3" "$4" > "$TMP/r.html"
  shoot "$TMP/r.html" "$2" "$3" "$4"
}

mkdir -p "$LOGO/png"
for svg in "$LOGO"/radiant-robotics-*.svg; do
  name="$(basename "$svg" .svg)"
  read -r w h < <(sed -nE 's/.*viewBox="0 0 ([0-9.]+) ([0-9.]+)".*/\1 \2/p' "$svg" | head -1)
  case "$name" in
    *horizontal*) W=2400 ;;
    *stacked*) W=2000 ;;
    *) W=1024 ;;
  esac
  H=$(awk -v W="$W" -v w="$w" -v h="$h" 'BEGIN { printf "%d", W * h / w + 0.5 }')
  render_svg "$svg" "$LOGO/png/$name.png" "$W" "$H"
done

TILE="$LOGO/radiant-robotics-mark-tile.svg"
cp "$TILE" "$ROOT/favicon.svg"
render_svg "$TILE" "$ROOT/apple-touch-icon.png" 180 180
render_svg "$TILE" "$ROOT/assets/img/icon-512.png" 512 512
for s in 16 32 48; do render_svg "$TILE" "$TMP/icon-$s.png" "$s" "$s"; done
magick "$TMP/icon-16.png" "$TMP/icon-32.png" "$TMP/icon-48.png" "$ROOT/favicon.ico"

shoot "$ROOT/brand/tools/og-image.html" "$ROOT/assets/img/og-image.png" 1200 630

rm -rf "$TMP"
echo "Done."
