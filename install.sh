#!/usr/bin/env bash
# AI Radar installer (macOS).  https://github.com/7hrn1/macos-ai-radar-widget
#   ./install.sh                 install / upgrade (keeps your prefs.json + apps.json)
#   ./install.sh --voice         also set up push-to-talk voice (sox, whisper.cpp, Hammerspoon)
#   ./install.sh --dest DIR      install into DIR instead of Übersicht's widgets folder (for testing)
#   ./install.sh --skip-deps     don't brew-install anything
#   ./install.sh --no-launch     don't start/refresh Übersicht or run the first fetch
set -euo pipefail

VOICE=0; SKIP_DEPS=0; NO_LAUNCH=0; DEST=""
while [ $# -gt 0 ]; do case "$1" in
  --voice) VOICE=1;; --skip-deps) SKIP_DEPS=1;; --no-launch) NO_LAUNCH=1;; --dest) DEST="${2:?--dest needs a path}"; shift;;
  -h|--help) sed -n '2,8p' "$0"; exit 0;; *) echo "unknown option: $1" >&2; exit 2;; esac; shift; done

say() { printf '\033[1;35m▸\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m✗\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(uname)" = "Darwin" ] || die "AI Radar's widgets run on macOS (Übersicht)."
HERE="$(cd "$(dirname "$0")" && pwd)"
WIDGETS="${DEST:-$HOME/Library/Application Support/Übersicht/widgets}"
TARGET="$WIDGETS/ai-radar"

# ---- python (>= 3.9) --------------------------------------------------------------------------
PY="$(command -v python3 || true)"
[ -n "$PY" ] || die "python3 not found. Install it first:  brew install python"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || die "Python 3.9+ required (found $("$PY" --version))."
# the macOS /usr/bin/python3 stub pops an Xcode dialog on a fresh Mac — prefer a real one
if [ "$PY" = "/usr/bin/python3" ] && ! xcode-select -p >/dev/null 2>&1; then die "Only the Xcode stub python3 was found. Install a real one:  brew install python"; fi
say "Python: $PY ($("$PY" --version))"

# ---- dependencies ----------------------------------------------------------------------------
if [ "$SKIP_DEPS" = 0 ] && [ -z "$DEST" ]; then
  command -v brew >/dev/null 2>&1 || die "Homebrew is needed to install Übersicht. See https://brew.sh (or re-run with --skip-deps if you already have it)."
  [ -d "/Applications/Übersicht.app" ] || { say "Installing Übersicht…"; brew install --cask ubersicht; }
fi
[ -n "$DEST" ] || [ -d "/Applications/Übersicht.app" ] || warn "Übersicht.app not found in /Applications — the widgets won't show until it's installed."

# ---- copy + generate -------------------------------------------------------------------------
say "Installing to: $TARGET"
mkdir -p "$TARGET"
rsync -a --exclude 'prefs.json' --exclude 'apps.json' --exclude 'feed.json' --exclude 'img/' --exclude 'icons/' "$HERE/widget/" "$TARGET/"
[ -f "$TARGET/prefs.json" ] || cp "$TARGET/prefs.example.json" "$TARGET/prefs.json"
[ -f "$TARGET/apps.json" ]  || cp "$TARGET/apps.example.json" "$TARGET/apps.json"
chmod +x "$TARGET"/*.py "$TARGET"/*.sh
for f in feed.jsx quick.jsx strip.jsx; do
  # placeholders -> real paths (| as delimiter; paths never contain it)
  sed -i '' -e "s|__DIR__|$TARGET|g" -e "s|__PYTHON__|$PY|g" -e "s|__WIDGET__|ai-radar|g" "$TARGET/$f"
done
sed -i '' -e "s|__WIDGET__|ai-radar|g" "$TARGET/radar.html" 2>/dev/null || true

# ---- the `radar` command ---------------------------------------------------------------------
sed -i '' "1s|.*|#!$PY|" "$TARGET/radar_cli.py"
if [ -z "$DEST" ]; then      # test installs (--dest) never touch anything outside their folder
  mkdir -p "$HOME/.local/bin"
  ln -sf "$TARGET/radar_cli.py" "$HOME/.local/bin/radar"
  case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) warn "Add ~/.local/bin to your PATH to use the \`radar\` command:  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc";; esac
fi

# ---- first fetch -----------------------------------------------------------------------------
if [ "$NO_LAUNCH" = 0 ]; then
  say "Fetching app icons…";        "$PY" "$TARGET/engine.py" --fetch-icons || warn "icon fetch failed (non-fatal)"
  say "First data fetch (≈15 s)…";  "$PY" "$TARGET/engine.py" --force || warn "first fetch failed — run \`radar doctor\`"
fi

# ---- optional voice ---------------------------------------------------------------------------
if [ "$VOICE" = 1 ] && [ -n "$DEST" ]; then warn "--voice is skipped in --dest test mode";
elif [ "$VOICE" = 1 ]; then
  say "Setting up voice (push-to-talk, all local)…"
  [ "$SKIP_DEPS" = 1 ] || { command -v brew >/dev/null || die "Homebrew needed for --voice"; brew install sox whisper-cpp; brew install --cask hammerspoon; }
  MODEL="$HOME/.local/share/radar/models/ggml-base.en.bin"; mkdir -p "$(dirname "$MODEL")"
  [ -s "$MODEL" ] || { say "Downloading the speech model (141 MB)…"; curl -L --fail -# -o "$MODEL" "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"; }
  mkdir -p "$HOME/.hammerspoon"; cp "$HERE/hammerspoon/ai-radar.lua" "$HOME/.hammerspoon/ai-radar.lua"
  if [ ! -f "$HOME/.hammerspoon/init.lua" ]; then echo 'require("ai-radar")' > "$HOME/.hammerspoon/init.lua"
  elif ! grep -q 'ai-radar' "$HOME/.hammerspoon/init.lua"; then warn 'Add this line to ~/.hammerspoon/init.lua:  require("ai-radar")'; fi
  [ "$NO_LAUNCH" = 1 ] || open -a Hammerspoon || true
  say "Hold ⌥ Space and speak. macOS will ask for Microphone access for Hammerspoon the first time."
fi

# ---- start ------------------------------------------------------------------------------------
if [ "$NO_LAUNCH" = 0 ] && [ -z "$DEST" ]; then
  open -a "Übersicht" || true; sleep 2
  osascript -e 'tell application id "tracesOf.Uebersicht" to refresh' >/dev/null 2>&1 || true
fi
echo
say "Done.  Edit your apps in  $TARGET/apps.json  and your interests in  $TARGET/prefs.json"
say "Try:  radar doctor     radar ask \"boost voice cloning\"     radar ask \"open gmail\""
