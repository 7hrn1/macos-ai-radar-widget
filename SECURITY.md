# Security policy

AI Radar renders and opens links that come from third-party feeds, so we treat all feed content as untrusted:
only plain `http(s)` URLs are accepted (`engine.safe_url`, re-checked in each widget and in `radar.html`), shell arguments are single-quoted,
and voice/LLM output can only produce a schema-validated preferences patch.

**Report a vulnerability** privately via GitHub → *Security* → *Report a vulnerability* (or open a minimal issue asking for a contact, without details). Please don't post exploits publicly before a fix is released.
Particularly interesting: anything that makes a feed item, README, or voice transcript run a command, open a non-web URL, or write outside the widget folder.
