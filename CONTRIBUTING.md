# Contributing

```bash
python3 -m unittest discover -s tests -v     # all tests, no network needed
./install.sh --dest /tmp/ar-test/widgets --skip-deps    # full install into a scratch folder (never touches your real setup)
```
- Keep it dependency-free (Python stdlib only) and local-first. New network calls must be listed in the README's *Privacy* section.
- Anything that handles feed content must go through `engine.safe_url` / `esc()`; add a test.
- Widgets are compiled by Übersicht with its own Babel: **no `<>…</>` fragments** (they need a global `React` and fail with "Can't find variable: React").
- UI sizes use the `calc(N * var(--u))` scale unit so the layout scales with screen width — don't hard-code px (except 1px borders).
- New sources: add a `lane_*` function returning items (`t,u,s,d,b,c,st,raw_img`), register it in `build()`, and a test for any parsing.
- Widget boxes are absolutely positioned and can overlap other widgets' areas. Give any large container `pointer-events: none` and re-enable it only on the parts that are interactive, or it will swallow clicks meant for widgets underneath.
