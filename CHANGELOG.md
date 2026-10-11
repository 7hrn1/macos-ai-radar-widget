# Changelog

## 0.1.1
- Opening "See all" now adds a version stamp so a stale open tab can never show an old layout
- "See all" page: every card now has the same height (fixed image area, title, fading text, one-line tags, pinned footer) for a balanced grid
- `radar doctor` no longer reports a running Übersicht as stopped

## 0.1.0 — first public release
- Five lanes with carousel cards, local image cache, full "See all" page with search and infinite scroll
- Prefs-driven ranking (boost/mute/min stars), per-lane source health, `radar doctor`
- Optional free voice control (hold ⌥ Space): local whisper.cpp + local rules, optional LLM fallback with a schema-validated patch
- Quick-access app icons, markets strip, system meters; responsive layout for any screen width
- Installer / uninstaller, 26 unit tests, CI
