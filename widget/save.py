#!/usr/bin/env python3
"""Append a bookmarked item to ~/Documents/ai-radar-saved.md.  Arg: base64 of JSON {n, u, d}."""
import base64, datetime, json, os, re, sys
from urllib.parse import urlsplit

def one_line(s, n):
    return re.sub(r'\s+', ' ', re.sub(r'[\[\]`*_<>]', '', str(s or ''))).strip()[:n]

try:
    it = json.loads(base64.b64decode(sys.argv[1]).decode('utf-8'))
except Exception:
    sys.exit(1)
u = str(it.get('u') or '').strip()
if urlsplit(u).scheme not in ('http', 'https'):
    sys.exit(1)
line = f"- [ ] **{one_line(it.get('n'), 160)}** — {one_line(it.get('d'), 200)}\n  <{u.replace('>', '%3E').replace(' ', '%20')}> _(saved {datetime.datetime.now():%Y-%m-%d %H:%M})_\n"
path = os.path.expanduser('~/Documents/ai-radar-saved.md')
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'a', encoding='utf-8') as f:
    f.write(line)
