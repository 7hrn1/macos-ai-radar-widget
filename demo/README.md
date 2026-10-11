# Demo renderer

Builds `docs/demo.gif` from the **real** widgets, reproducibly — no screen recording, nothing from your own desktop.

```bash
cd demo && ./build.sh        # needs Node 18+, Python 3.9+, Google Chrome and a network connection (live data, fetched once)
# env: CHROME=/path/to/chrome  WIDTH=840  FPS=8  PORT=8890
```

**What it does**
1. Installs a scratch copy of the widgets with `install.sh --dest` (the example shortcuts, today's live feed) — your real setup is never touched.
2. Bundles the real `feed.jsx`, `quick.jsx` and `strip.jsx` so they render in a plain browser page, stacked like Übersicht stacks them.
3. `render.mjs` drives headless Chrome frame by frame: carousel animations are *scrubbed* (3× speed), the cursor path is scripted, and the real "See all" page is scrolled and searched. Same input → same frames.
4. `make_gif.py` assembles the frames into an optimised GIF (one shared palette, crossfade between pages).

**What is real and what is staged**
- Real: the three widgets, the data, the images, the hover effects, the "See all" page and its search.
- Staged: the cursor and the ⌥ Space key badge are overlays; captions are overlays; the wallpaper is an abstract gradient.
- The voice panel images in `assets/` are real snapshots of the Hammerspoon panel (captured from Hammerspoon's own canvas while running a test phrase). A real hotkey press is not recorded.

**Tuning:** the whole script is in `render.mjs` (scenes, timings, captions, cursor path). File size is mostly `WIDTH`, `FPS` and the number of colours in `make_gif.py`. Don't commit a new GIF on every tweak — each one adds several MB to git history.
