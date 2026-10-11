#!/usr/bin/env bash
# Removes AI Radar. Your prefs.json / apps.json are copied to ~/ai-radar-backup first.
set -euo pipefail
TARGET="${1:-$HOME/Library/Application Support/Übersicht/widgets/ai-radar}"
[ -d "$TARGET" ] || { echo "nothing to remove at: $TARGET"; exit 0; }
BK="$HOME/ai-radar-backup"; mkdir -p "$BK"
for f in prefs.json apps.json; do [ -f "$TARGET/$f" ] && cp "$TARGET/$f" "$BK/"; done
rm -rf "$TARGET"
[ -L "$HOME/.local/bin/radar" ] && rm "$HOME/.local/bin/radar"
rm -f "$HOME/.hammerspoon/ai-radar.lua"
echo "Removed. Config backup: $BK"
echo "Left in place (remove manually if you want): Übersicht.app, Hammerspoon, ~/.local/share/radar (speech model), the 'require(\"ai-radar\")' line in ~/.hammerspoon/init.lua"
