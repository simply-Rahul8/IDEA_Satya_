#!/usr/bin/env bash
# Render the static prototypes to PNG with headless Chrome (no network).
# usage (from docs/design/): tools/shots.sh page.html width height [theme] [out-name]
# Chrome's headless window can't go below ~500px wide, so widths < 500 are rendered
# inside tools/frame.html, whose iframe has a true 360px layout viewport.
# Windows host: finds Chrome in its default install path; override with CHROME=...
set -euo pipefail
CHROME="${CHROME:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
page="$1"; w="$2"; h="$3"; theme="${4:-light}"; out="${5:-${page%.html}-${w}-${theme}}"
root="$(pwd -W 2>/dev/null || pwd)"
if [ "$w" -lt 500 ]; then
  url="file:///${root}/tools/frame.html?src=../${page}%3Fdemo%26theme%3D${theme}&w=${w}&h=${h}"; win="500,${h}"
else
  url="file:///${root}/${page}?demo&theme=${theme}"; win="${w},${h}"
fi
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --window-size="${win}" --virtual-time-budget=3000 \
  --screenshot="${root}/screenshots/${out}.png" "$url" >/dev/null 2>&1
[ -s "screenshots/${out}.png" ] && echo "screenshots/${out}.png" || { echo "FAILED ${out}" >&2; exit 1; }
