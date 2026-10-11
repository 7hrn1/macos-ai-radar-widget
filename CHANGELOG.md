# Changelog

## 0.1.4
- Voice: an on-screen panel now shows every stage (listening → transcribing → what it heard → working → the reply and what changed) instead of vanishing after 3 s; replies are also spoken. New pref `voice_feedback`: both | text | speech
- Fix: speech-to-text adds a final “.”/“?”, which made most spoken commands miss the instant local rules and go to the slower LLM path — punctuation is now ignored
- Fix: LLM-routed requests now open the matching lane (agents → Agents, video tools → Creator)
- `claude -p` is started with stdin closed (no 3 s stall when launched from Hammerspoon)

## 0.1.3
- Shortcut icons: smoother, cleaner hover — lift + a thin app-tinted ring and soft shadow (animated with box-shadow/transform only; the stacked glow filters flashed and re-rendered every frame)

## 0.1.2
- Fix: the app-shortcut icons could be unclickable — the feed widget's (empty) header area covered them and swallowed the clicks. The feed container is now click-through, the shortcuts sit on a higher layer, and the display-only markets strip never blocks clicks.

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
