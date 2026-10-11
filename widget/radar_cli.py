#!/usr/bin/env python3
"""radar — control AI Radar by text or voice.
  radar ask "mute crypto"   radar voice start|stop   radar refresh   radar prefs   radar doctor
Simple requests are handled by local rules (free, instant). Open-ended ones go to `claude -p`
(your Claude plan, Haiku, no tools) which may only return a validated prefs patch."""
import json, os, re, shutil, signal, subprocess, sys, time, urllib.parse
os.environ['PATH'] = ':'.join([os.path.expanduser('~/.local/bin'), '/opt/homebrew/bin', '/usr/local/bin', '/usr/bin', '/bin', os.environ.get('PATH', '')])
W = os.path.dirname(os.path.realpath(__file__))      # the installed widget folder (works through the ~/.local/bin/radar symlink)
WIDGET = os.path.basename(W)
PORT = 41416                                        # Übersicht's default server port
PREFS, FEED, APPS = os.path.join(W, 'prefs.json'), os.path.join(W, 'feed.json'), os.path.join(W, 'apps.json')
R = os.path.expanduser('~/.local/share/radar'); TMP = os.path.join(R, 'tmp'); MODEL = os.path.join(R, 'models/ggml-base.en.bin')
WAV, PIDF, LOG = os.path.join(TMP, 'cmd.wav'), os.path.join(TMP, 'rec.pid'), os.path.join(R, 'radar.log')
LANES = {'labs': 'labs', 'lab': 'labs', 'news': 'labs', 'releases': 'releases', 'release': 'releases', 'launches': 'launches', 'launch': 'launches', 'products': 'launches',
         'product': 'launches', 'agents': 'repos', 'agent': 'repos', 'skills': 'repos', 'repos': 'repos', 'repositories': 'repos', 'github': 'repos', 'creator': 'creator',
         'creators': 'creator', 'creative': 'creator', 'models': 'creator'}
os.makedirs(TMP, exist_ok=True)

def log(*a):
    open(LOG, 'a').write(time.strftime('%F %T ') + ' '.join(str(x) for x in a) + '\n')
def load():
    for p in (PREFS, PREFS.replace('prefs.json', 'prefs.example.json')):
        try:
            with open(p) as f: return json.load(f)
        except Exception: continue
    return {}
def save(p):
    with open(PREFS + '.tmp', 'w') as f: json.dump(p, f, indent=2, ensure_ascii=False)
    os.replace(PREFS + '.tmp', PREFS)
def say(t):
    log('SAY', t); print(t)
    if not os.environ.get('RADAR_NO_SAY'): subprocess.Popen(['say', '-r', '195', '--', t], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def sound(n):
    if not os.environ.get('RADAR_NO_SAY'): subprocess.Popen(['afplay', f'/System/Library/Sounds/{n}.aiff'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def open_url(u):
    log('OPEN', u)
    if not os.environ.get('RADAR_NO_OPEN'): subprocess.Popen(['open', u])
def apps_cfg():
    for p in (APPS, APPS.replace('apps.json', 'apps.example.json')):
        try:
            with open(p) as f: return json.load(f)
        except Exception: continue
    return {}
def find_app(name):
    cfg = apps_cfg()
    if not cfg: return None
    n = re.sub(r'\s+', ' ', name.lower().strip())
    for a in cfg.get('apps', []):
        if n == a['name'].lower() or n in [x.lower() for x in a.get('aliases', [])]: return a, cfg.get('chrome_profile', 'Default')
    return None
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
def open_app(a, profile):
    log('APP', a['name'], a['url'])
    if os.environ.get('RADAR_NO_OPEN') or not re.match(r'https?://', a['url']): return
    cmd = [CHROME, f'--profile-directory={profile}', a['url']] if os.path.exists(CHROME) else ['open', a['url']]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
def page(lane='', q=''):
    qs = {k: v for k, v in (('lane', lane), ('q', q)) if v}
    return f'http://127.0.0.1:{PORT}/{WIDGET}/radar.html' + ('?' + urllib.parse.urlencode(qs) if qs else '')
def refresh_bg():
    if os.environ.get('RADAR_NO_REFRESH'): return
    subprocess.Popen([sys.executable, os.path.join(W, 'engine.py'), '--force'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
def feed():
    try:
        with open(FEED) as f: return json.load(f)
    except Exception: return {'lanes': {}}

def apply_patch(p, patch):
    """validate + clamp; returns list of human-readable changes"""
    ch = []
    def lst(key, add, rem):
        cur = list(p.get(key, []))
        for x in patch.get(add, []) or []:
            x = str(x).strip().lower()[:40]
            if x and x not in [c.lower() for c in cur]: cur.append(x); ch.append(f'{add.split("_")[0]} {x}')
        for x in patch.get(rem, []) or []:
            x = str(x).strip().lower()
            n = [c for c in cur if c.lower() != x]
            if len(n) != len(cur): cur = n; ch.append(f'removed {x}')
        p[key] = cur[:40]
    lst('boost', 'boost_add', 'boost_remove'); lst('mute', 'mute_add', 'mute_remove')
    for key, lo, hi in (('min_stars', 0, 100000), ('desk_items', 3, 14), ('repo_days', 1, 90)):
        v = patch.get(key)
        if isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi and p.get(key) != v: p[key] = v; ch.append(f'{key} {v}')
    for k, v in (patch.get('lanes') or {}).items():
        if k in LANES.values() and isinstance(v, bool) and p.setdefault('lanes', {}).get(k, True) != v: p['lanes'][k] = v; ch.append(f'{k} {"on" if v else "off"}')
    rr = list(p.get('releases_repos', []))
    for x in patch.get('releases_repos_add', []) or []:
        if re.fullmatch(r'[\w.-]+/[\w.-]+', str(x)) and x not in rr: rr.append(x); ch.append(f'tracking {x}')
    for x in patch.get('releases_repos_remove', []) or []:
        if x in rr: rr.remove(x); ch.append(f'stopped tracking {x}')
    p['releases_repos'] = rr
    return ch

def brief(lane=None, n=3):
    L = feed().get('lanes', {}); items = (L.get(lane, []) if lane else sorted([i for v in L.values() for i in v], key=lambda i: -i.get('score', 0)))[:n]
    if not items: return "I don't have anything yet. Say refresh."
    return ('Top in ' + {'repos': 'agents', 'labs': 'labs', 'releases': 'releases', 'launches': 'launches', 'creator': 'creator tools'}[lane] + ': ' if lane else 'Top stories: ') + '. '.join(re.sub(r'[^\w\s.,\'&:/-]', ' ', i['t'])[:70] for i in items)

def rules(t):
    """-> (patch, open_lane, query, say) or None"""
    s = re.sub(r'[^\w\s\'./+-]', ' ', t.lower()).strip(); s = re.sub(r'^(hey )?(radar|jarvis)[, ]*', '', s); s = re.sub(r'^(please|can you|could you|would you)\s+', '', s)
    if re.fullmatch(r'(refresh|reload|update)( the)?( radar| feed| everything)?( now)?', s): return ({}, None, None, 'Refreshing the radar now.', True)
    m = re.fullmatch(r'(open|launch|go to|take me to|pull up|show me|bring up|start)( up)?( my| the)?\s+(.+?)( app| tab| page| website)?', s)
    if m and find_app(m.group(4)): return ({}, None, None, 'Opening ' + find_app(m.group(4))[0]['name'] + '.', False, find_app(m.group(4)))
    m = re.fullmatch(r'(brief me|catch me up|what\'?s new|what is new|top stories|what\'?s happening)( in| on| for)?( the)?\s*(\w+)?', s)
    if m: return ({}, None, None, brief(LANES.get((m.group(4) or '').lower())), False)
    m = re.fullmatch(r'(show|open|go to|take me to|pull up)( me)?( only)?( the)?( all| everything| full| radar| full radar)?( page| view| feed)?', s)
    if m and (m.group(5) or m.group(6) or s.startswith(('open', 'go to'))): return ({}, '', None, 'Opening the full radar.', False)
    m = re.fullmatch(r'(show|open|go to|take me to|pull up|list)( me)?( only)?( the)?( new| latest| top)?\s*(\w+)( page| section| lane| tab)?', s)
    if m and m.group(6) in LANES: return ({}, LANES[m.group(6)], None, 'Opening ' + m.group(6) + '.', False)
    m = re.fullmatch(r'(search|find|look)( for| up)?\s+(.+)', s)
    if m: return ({}, '', m.group(3), 'Searching for ' + m.group(3) + '.', False)
    m = re.fullmatch(r'(mute|hide|block|ignore|filter out|no more)\s+(.+)', s)
    if m: return ({'mute_add': [m.group(2)]}, None, None, 'Muted ' + m.group(2) + '.', True)
    m = re.fullmatch(r'(unmute|unhide|unblock|stop (muting|hiding))\s+(.+)', s)
    if m: return ({'mute_remove': [m.group(m.lastindex)]}, None, None, 'Unmuted ' + m.group(m.lastindex) + '.', True)
    m = re.fullmatch(r'(boost|focus on|more of|more|prioriti[sz]e|add topic|follow)\s+(.+)', s)
    if m: return ({'boost_add': [m.group(2)]}, None, None, 'Boosting ' + m.group(2) + '.', True)
    m = re.fullmatch(r'(less of|less|stop boosting|drop topic|unfollow|deprioriti[sz]e)\s+(.+)', s)
    if m: return ({'boost_remove': [m.group(2)]}, None, None, 'Dropped ' + m.group(2) + ' from your boosts.', True)
    m = re.search(r'(?:minimum|min|at least|over)\s+(\d[\d,]*)\s*(?:k\b)?\s*stars?', s)
    if m:
        v = int(m.group(1).replace(',', '')) * (1000 if re.search(r'\d\s*k\b', s) else 1); return ({'min_stars': v}, None, None, f'Minimum stars set to {v}.', True)
    m = re.search(r'(?:show|display|keep)\s+(\d+)\s+items?', s)
    if m: return ({'desk_items': int(m.group(1))}, None, None, f'Showing {m.group(1)} items per lane.', True)
    return None

SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['say'], 'properties': {
    'say': {'type': 'string'}, 'open_lane': {'type': 'string', 'enum': ['', 'labs', 'releases', 'launches', 'repos', 'creator']}, 'query': {'type': 'string'},
    'patch': {'type': 'object', 'additionalProperties': False, 'properties': {
        'boost_add': {'type': 'array', 'items': {'type': 'string'}}, 'boost_remove': {'type': 'array', 'items': {'type': 'string'}},
        'mute_add': {'type': 'array', 'items': {'type': 'string'}}, 'mute_remove': {'type': 'array', 'items': {'type': 'string'}},
        'min_stars': {'type': 'integer'}, 'desk_items': {'type': 'integer'}, 'repo_days': {'type': 'integer'},
        'lanes': {'type': 'object', 'additionalProperties': {'type': 'boolean'}},
        'releases_repos_add': {'type': 'array', 'items': {'type': 'string'}}, 'releases_repos_remove': {'type': 'array', 'items': {'type': 'string'}}}}}}

def llm(text, p):
    L = feed().get('lanes', {}); titles = '\n'.join(f"- [{k}] {i['t'][:90]}" for k, v in L.items() for i in v[:6])
    prompt = ("You are the voice controller for a personal AI-news desktop dashboard. The user's spoken request was transcribed (it may contain mishearings). "
              "Turn it into: a `patch` to their preferences (only fields that must change), optionally `open_lane`/`query` to open the full browse page, and `say` = one short spoken sentence (<=22 words) confirming what you did or answering a question using the headlines below. "
              "boost_* = topics to rank higher, mute_* = topics to hide. If the request is unclear or unrelated, change nothing and say you didn't catch it.\n\n"
              f"Current prefs: {json.dumps({k: p.get(k) for k in ('boost', 'mute', 'min_stars', 'desk_items', 'repo_days', 'lanes')})}\nCurrent top headlines:\n{titles}\n\nRequest: {text}")
    cmd = ['claude', '-p', prompt, '--model', 'claude-haiku-4-5', '--tools', '', '--no-session-persistence', '--disable-slash-commands', '--setting-sources', '',
           '--output-format', 'json', '--json-schema', json.dumps(SCHEMA)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=90, cwd=TMP); log('LLM rc', r.returncode, r.stderr[:200])
    out = json.loads(r.stdout)
    res = out.get('structured_output') or out.get('result')
    if isinstance(res, str): res = json.loads(res)
    return res

def ask(text):
    text = (text or '').strip(); log('ASK', text)
    if not text or re.fullmatch(r'[\[\(].*[\]\)]', text) or len(text) < 3: return
    p = load(); r = rules(text)
    if r is None:
        try: o = llm(text, p)
        except Exception as e: log('LLM FAIL', repr(e)); say("Sorry, I couldn't reach Claude for that one."); return
        patch, lane, q, msg, needs = o.get('patch') or {}, o.get('open_lane'), o.get('query'), o.get('say') or 'Done.', None
    else:
        patch, lane, q, msg, needs = r[0], r[1], r[2], r[3], r[4]
        if len(r) > 5: open_app(*r[5]); say(msg); return
    changed = apply_patch(p, patch) if patch else []
    if changed: save(p); log('PATCH', changed)
    if changed or needs is True: refresh_bg()
    if lane is not None and (lane or q or True) and (r is None and (lane or q) or r is not None and lane is not None): open_url(page(lane or '', q or ''))
    say(msg)

def voice(action):
    if action == 'start':
        if os.path.exists(PIDF):
            try: os.kill(int(open(PIDF).read()), 0); return
            except Exception: pass
        sound('Tink'); pr = subprocess.Popen(['rec', '-q', '-r', '16000', '-c', '1', '-b', '16', WAV, 'trim', '0', '45'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        open(PIDF, 'w').write(str(pr.pid)); log('REC start', pr.pid)
    elif action == 'stop':
        try: pid = int(open(PIDF).read()); os.remove(PIDF)
        except Exception: return
        try: os.kill(pid, signal.SIGINT)
        except Exception: pass
        time.sleep(0.35); sound('Pop')
        r = subprocess.run(['whisper-cli', '-m', MODEL, '-f', WAV, '-nt', '-np', '-t', '4', '-l', 'en'], capture_output=True, text=True, timeout=60)
        try: os.remove(WAV)                          # the recording is deleted as soon as it's transcribed
        except OSError: pass
        text = re.sub(r'\s+', ' ', r.stdout).strip(); log('HEARD', repr(text)); print('heard:', text)
        ask(text)

def doctor():
    """Self-check: tells you what works and what to fix."""
    ok = lambda b: '✓' if b else '✗'
    def has(cmd): return shutil.which(cmd) is not None
    print(f'AI Radar — doctor   (widget folder: {W})\n')
    ub = os.path.exists('/Applications/Übersicht.app')
    srv = False
    try: import urllib.request; srv = urllib.request.urlopen(f'http://127.0.0.1:{PORT}/', timeout=3).status == 200
    except Exception: pass
    print(f'{ok(ub)} Übersicht installed      {ok(srv)} running (its server answers on :{PORT})')
    for f in ('feed.jsx', 'quick.jsx', 'strip.jsx', 'engine.py', 'radar.html'): print(f'{ok(os.path.exists(os.path.join(W, f)))} {f}', end='   ')
    print()
    fd = feed(); age = None
    try: age = int((time.time() - os.path.getmtime(FEED)) / 60)
    except Exception: pass
    print(f'\n{ok(age is not None)} feed.json  ' + (f'{age} min old, {sum(fd.get("counts", {}).values())} items' if age is not None else 'missing — run: radar refresh'))
    h = fd.get('health', {})
    for lane, v in (h.get('lanes') or {}).items(): print(f'   {ok(v["n"] > 0 and not v["error"])} {lane:9s} {v["n"]:3d} items  {v["ms"]:5d} ms  {v["error"]}')
    fh = h.get('failing_hosts') or {}
    if fh:
        print('   ℹ optional fetches that failed (usually harmless — article pages that block bots, repos without releases…):')
        for host, v in fh.items(): print(f'       {host}: {v["fail"]} failed ({v["error"]})')
    if h and not h.get('github_token'): print('   ⚠ no GitHub token — anonymous limit is 60 requests/hour. Fix: `gh auth login` or export GITHUB_TOKEN')
    print(f'\nVoice (optional):  {ok(has("rec"))} sox   {ok(has("whisper-cli"))} whisper-cli   {ok(os.path.exists(MODEL))} model   {ok(os.path.exists(os.path.expanduser("~/.hammerspoon/ai-radar.lua")))} Hammerspoon hotkey')
    print(f'Smart replies:     {ok(has("claude"))} claude CLI (only for open-ended voice requests; everything else is local rules)')
    print(f'Apps:              {ok(os.path.exists(CHROME))} Google Chrome   {ok(os.path.exists(os.path.join(W, "icons")))} icons')

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__)
    elif a[0] == 'ask': ask(' '.join(a[1:]))
    elif a[0] == 'voice' and len(a) > 1: voice(a[1])
    elif a[0] == 'refresh': refresh_bg(); say('Refreshing the radar now.')
    elif a[0] == 'prefs': print(json.dumps(load(), indent=2, ensure_ascii=False))
    elif a[0] == 'say': say(' '.join(a[1:]))
    elif a[0] == 'doctor': doctor()
    else: print(__doc__)
