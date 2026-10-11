#!/usr/bin/env bash
# Builds docs/demo.gif from the real widgets. Needs: Node 18+, Python 3.9+, Google Chrome. Network (live data) is used once.
#   ./build.sh              → ../docs/demo.gif          (env: CHROME=/path/to/chrome  WIDTH=960  FPS=10  PORT=8890)
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"; WORK="${DEMO_WORK:-$PWD/.work}"; PORT="${PORT:-8890}"; WIDTH="${WIDTH:-840}"; FPS="${FPS:-8}"
say() { printf '\033[1;35m▸\033[0m %s\n' "$*"; }
[ -d "${CHROME_APP:-/Applications/Google Chrome.app}" ] || [ -n "${CHROME:-}" ] || { echo "Google Chrome not found (set CHROME=/path/to/chrome)"; exit 1; }

rm -rf "$WORK"; mkdir -p "$WORK/site/out" "$WORK/site/data"
say "Installing a scratch copy (example shortcuts, live data) — your real setup is untouched"
"$ROOT/install.sh" --dest "$WORK/widgets" --skip-deps >/dev/null
INST="$WORK/widgets/ai-radar"
ln -s "$INST" "$WORK/site/ai-radar"
# demo-only: keep items that have a real picture (no grey placeholder tiles in the clip), in both the widget feed and the "See all" page
python3 - "$INST/feed.json" "$WORK/site/data/feed.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d['lanes'] = {k: [i for i in v if i.get('img')] for k, v in d['lanes'].items()}
d['counts'] = {k: len(v) for k, v in d['lanes'].items()}
json.dump(d, open(sys.argv[1], 'w')); json.dump(d, open(sys.argv[2], 'w'))
PY
cp "$INST/apps.json" "$WORK/site/data/apps.json"
python3 "$INST/rail.py" > "$WORK/site/data/rail.json"
cp -R assets "$WORK/site/assets"; cp stage.html "$WORK/site/stage.html"

say "Bundling the widgets for a plain browser page"
rm -rf widgets; mkdir widgets; cp "$INST/feed.jsx" "$INST/quick.jsx" "$INST/strip.jsx" widgets/
[ -d node_modules ] || npm install --no-audit --no-fund --silent
npx esbuild harness.jsx --bundle --format=esm --target=es2022 --jsx=automatic --alias:uebersicht=./uebersicht-stub.js \
  --define:process.env.NODE_ENV=\"production\" --outfile="$WORK/site/out/harness.js" --log-level=error

say "Rendering frames (headless Chrome)"
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$WORK/site" >/dev/null 2>&1 & SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1
node render.mjs --site "http://127.0.0.1:$PORT" --out "$WORK/frames" --fps "$FPS"

say "Encoding the GIF"
python3 -m venv "$WORK/venv" >/dev/null && "$WORK/venv/bin/pip" install -q pillow
"$WORK/venv/bin/python" make_gif.py "$WORK/frames" "$ROOT/docs/demo.gif" --width "$WIDTH" --fps "$FPS"
