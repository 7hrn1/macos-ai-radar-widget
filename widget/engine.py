#!/usr/bin/env python3
"""AI Radar engine: gathers every lane, scores by your prefs, caches images locally, writes feed.json.

usage: engine.py [--force] [--fetch-icons]
  (no flag)     refresh only if feed.json is older than prefs.refresh_minutes
  --force       refresh now
  --fetch-icons download the app icons listed in apps.json into icons/
"""
import collections, hashlib, html, json, math, os, re, shutil, ssl, subprocess, sys, threading, time, urllib.parse, urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
WIDGET = os.path.basename(HERE)          # folder name Übersicht serves us under
IMG = os.path.join(HERE, 'img'); FEED = os.path.join(HERE, 'feed.json'); PREFS = os.path.join(HERE, 'prefs.json'); APPS = os.path.join(HERE, 'apps.json')
CTX = ssl.create_default_context(cafile='/etc/ssl/cert.pem') if os.path.exists('/etc/ssl/cert.pem') else ssl.create_default_context()
UA = {'User-Agent': 'Mozilla/5.0'}
MAXLANE = 25

def prefs():
    for p in (PREFS, PREFS.replace('prefs.json', 'prefs.example.json')):
        try:
            with open(p) as f: return json.load(f)
        except Exception: continue
    return {}

HOSTS = collections.defaultdict(lambda: {'ok': 0, 'fail': 0, 'error': ''})
_lock = threading.Lock()

def get(url, headers=None, t=10):
    host = urllib.parse.urlparse(url).netloc
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    err = None
    for attempt in (1, 2):                      # one retry for flaky network / TLS hiccups; HTTP 4xx is final
        try:
            with urllib.request.urlopen(req, timeout=t, context=CTX) as r:
                data = r.read()
            with _lock: HOSTS[host]['ok'] += 1
            return data
        except urllib.error.HTTPError as e:
            err = e
            if e.code < 500: break
        except Exception as e:
            err = e
        time.sleep(0.4)
    with _lock: HOSTS[host]['fail'] += 1; HOSTS[host]['error'] = f'{type(err).__name__}: {err}'[:140]
    raise err


def safe_url(u):
    """Only plain http(s) links may reach the UI or a shell. Everything else is dropped; the rest is percent-encoded."""
    try:
        p = urllib.parse.urlsplit((u or '').strip())
        if p.scheme not in ('http', 'https') or not re.fullmatch(r'[A-Za-z0-9.\-:@\[\]_]+', p.netloc or ''): return ''
        keep = "/%:@!$&()*+,;=~-._"
        return urllib.parse.urlunsplit((p.scheme, p.netloc, urllib.parse.quote(p.path, safe=keep), urllib.parse.quote(p.query, safe=keep + '?'), urllib.parse.quote(p.fragment, safe=keep + '?')))
    except Exception:
        return ''


def gh_headers():
    """Optional: a GitHub token (GITHUB_TOKEN / GH_TOKEN env, or `gh auth login`) lifts the 60 req/h anonymous limit."""
    h = {'Accept': 'application/vnd.github+json'}
    tok = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN') or ''
    if not tok:
        gh = shutil.which('gh') or ('/opt/homebrew/bin/gh' if os.path.exists('/opt/homebrew/bin/gh') else '')
        if gh:
            try: tok = subprocess.run([gh, 'auth', 'token'], capture_output=True, text=True, timeout=5).stdout.strip()
            except Exception: tok = ''
    if tok: h['Authorization'] = 'Bearer ' + tok
    return h

def clean(s, n=200):
    s = re.sub(r'<[^>]+>', ' ', s or ''); s = html.unescape(s); return re.sub(r'\s+', ' ', s).strip()[:n]

def parse_date(s):
    if not s: return None
    try: d = parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.fromisoformat(s.replace('Z', '+00:00'))
        except Exception: return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def kfmt(n):
    return ('%.1fM' % (n / 1e6)) if n >= 1e6 else ('%.1fk' % (n / 1000)) if n >= 1000 else str(n)

def meta(url):
    try: h = get(url, t=6).decode('utf-8', 'ignore')[:300000]
    except Exception: return {'desc': '', 'img': '', 'p': ''}
    def tag(*names):
        for n in names:
            m = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]*content=["\']([^"\']*)["\']' % re.escape(n), h, re.I) or \
                re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name)=["\']%s["\']' % re.escape(n), h, re.I)
            if m: return html.unescape(m.group(1)).strip()
        return ''
    para = ''
    for m in re.finditer(r'<p[^>]*>(.*?)</p>', h, re.S | re.I):
        t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))).strip()
        dm = re.search(r'\b[A-Z][a-z]{2} \d{1,2}, \d{4}\s+(.{60,})', t)
        if dm: t = dm.group(1)
        if len(t) > 110: para = t; break
    return {'desc': tag('og:description', 'description', 'twitter:description'), 'img': tag('og:image', 'twitter:image'), 'p': para}

def readme_snip(txt, n=300):
    txt = re.sub(r'^---.*?---', '', txt, count=1, flags=re.S); txt = re.sub(r'<!--.*?-->', '', txt, flags=re.S)
    txt = re.sub(r'```.*?```', '', txt, flags=re.S); txt = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', txt)
    txt = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', txt); txt = html.unescape(re.sub(r'<[^>]+>', ' ', txt))
    out = []
    for ln in txt.splitlines():
        ln = re.sub(r'^[#>*\-\s|]+', '', ln).strip(' *_`')
        if len(ln) < 35 or re.search(r'badge|shields\.io|license|^table of contents', ln, re.I): continue
        out.append(ln)
        if len(' '.join(out)) > n: break
    return ' '.join(out)[:n].rstrip()

def readme_image(txt, base):
    """first real raster image in a README (skip badges/svg), resolved to an absolute URL"""
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']|!\[[^\]]*\]\(([^)\s]+)', txt):
        u = (m.group(1) or m.group(2) or '').strip()
        if not u or re.search(r'badge|shields\.io|\.svg|buymeacoffee|githubusercontent\.com/u/|star-history|img\.shields', u, re.I): continue
        if u.startswith('//'): u = 'https:' + u
        if not u.startswith('http'): u = base + u.lstrip('./')
        return u
    return ''

def cache_img(url):
    """download -> resize with sips -> img/<hash>.jpg ; returns '/<widget>/img/<hash>.jpg' or ''"""
    if not url or not url.startswith('http'): return ''
    name = hashlib.sha1(url.encode()).hexdigest()[:14] + '.jpg'; dst = os.path.join(IMG, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 800: return '/' + WIDGET + '/img/' + name
    tmp = dst + '.dl'
    try:
        data = get(url, t=8)
        if len(data) < 800 or len(data) > 12_000_000: return ''
        open(tmp, 'wb').write(data)
        r = subprocess.run(['/usr/bin/sips', '-Z', '640', '-s', 'format', 'jpeg', '-s', 'formatOptions', '70', tmp, '--out', dst], capture_output=True, timeout=20)
        return '/' + WIDGET + '/img/' + name if r.returncode == 0 and os.path.exists(dst) else ''
    except Exception: return ''
    finally:
        if os.path.exists(tmp): os.remove(tmp)

def rss(name, url, limit=10):
    try: root = ET.fromstring(get(url))
    except Exception: return []
    ns = {'a': 'http://www.w3.org/2005/Atom'}; out = []
    for it in (root.findall('.//item') or root.findall('.//a:entry', ns))[:limit * 2]:
        def tx(*tags):
            for tg in tags:
                e = it.find(tg, ns) if tg.startswith('a:') else it.find(tg)
                if e is not None and (e.text or '').strip(): return e.text.strip()
            return ''
        link = tx('link')
        if not link:
            le = it.find('a:link', ns); link = le.get('href') if le is not None else ''
        d = parse_date(tx('pubDate', 'a:published', 'a:updated'))
        if d and link: out.append({'t': clean(tx('title', 'a:title'), 140), 'u': link, 's': name, 'd': d.isoformat(), 'x': clean(tx('description', 'a:summary', 'a:content'), 300)})
    return sorted(out, key=lambda x: x['d'], reverse=True)[:limit]

# ------------------------------------------------------------------ lanes
DEFAULT_LAB_FEEDS = [('OpenAI', 'https://openai.com/news/rss.xml'),
             ('Anthropic', 'https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml'),
             ('DeepMind', 'https://deepmind.google/blog/rss.xml'), ('Hugging Face', 'https://huggingface.co/blog/feed.xml'),
             ('Simon Willison', 'https://simonwillison.net/atom/everything/'), ('Latent Space', 'https://www.latent.space/feed')]
AI_KW = re.compile(r'\bai\b|llm|model|gpt|claude|gemini|agent|openai|anthropic|mcp|codex|inference|gpu|prompt|token|eval|rag|copilot|cursor|gemma|qwen|llama|diffusion|robot', re.I)

def lane_labs(P):
    feeds = [tuple(f) for f in (P.get('lab_feeds') or DEFAULT_LAB_FEEDS)] + [tuple(f) for f in P.get('extra_feeds', [])]
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda a: rss(*a, limit=10), feeds))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=21)).isoformat(); noise = ('[subscriber', 'subscriber exclusive', 'meetup')
    items = [i for r in res for i in r if i['d'] > cutoff and not any(n in i['t'].lower() for n in noise)
             and (i['s'] not in ('Simon Willison', 'Latent Space') or AI_KW.search(i['t']))]
    since = int(time.time()) - 2 * 86400
    def hn(q):
        try: return json.loads(get('https://hn.algolia.com/api/v1/search?' + urllib.parse.urlencode({'query': q, 'tags': 'story', 'numericFilters': f'created_at_i>{since},points>80', 'hitsPerPage': 5})))['hits']
        except Exception: return []
    with ThreadPoolExecutor(8) as ex: hits = [h for r in ex.map(hn, ['claude', 'gpt', 'gemini', 'llm', 'agent', 'mcp', 'openai', 'anthropic']) for h in r]
    seen = set()
    for h in sorted(hits, key=lambda h: h.get('points', 0), reverse=True):
        if h['objectID'] in seen or not h.get('title'): continue
        seen.add(h['objectID'])
        items.append({'t': h['title'][:140], 'u': h.get('url') or 'https://news.ycombinator.com/item?id=' + h['objectID'], 's': 'Hacker News', 'd': h['created_at'], 'x': '',
                      'st': ['▲ %s' % h.get('points', 0), '💬 %s' % h.get('num_comments', 0)], 'hn': h.get('points', 0)})
    items.sort(key=lambda x: x['d'], reverse=True)
    def enrich(i):
        if i.get('x') and len(i['x']) >= 120: m = {'desc': '', 'img': '', 'p': ''} if i['s'] != 'Hacker News' else meta(i['u'])
        else: m = meta(i['u'])
        generic = re.match(r'(Anthropic is an AI safety|OpenAI is an AI research|Google DeepMind)', m['desc'] or '')
        body = i['x'] if len(i.get('x', '')) >= 120 else ((m.get('p') if generic else '') or m['desc'] or i.get('x', ''))
        if not m['img'] and i.get('x') and len(i['x']) >= 120: m['img'] = meta(i['u'])['img']
        out = {'t': i['t'], 'u': i['u'], 's': i['s'], 'd': i['d'], 'b': body[:380], 'c': [i['s']], 'raw_img': m['img']}
        if i.get('st'): out['st'] = i['st']
        if i.get('hn'): out['hn'] = i['hn']
        return out
    with ThreadPoolExecutor(10) as ex: return list(ex.map(enrich, items[:40]))

def lane_launches(P):
    out = rss('Product Hunt', 'https://www.producthunt.com/feed?category=artificial-intelligence', 20)
    def enrich(i):
        tag = re.sub(r'\s*Discussion\s*\|\s*Link\s*$', '', i['x']).strip(); m = meta(i['u'])
        return {'t': i['t'], 'u': i['u'], 's': 'Product Hunt', 'd': i['d'], 'b': (m['desc'] if len(m['desc']) > len(tag) else tag)[:340], 'c': ['Launch', 'AI'], 'raw_img': m['img']}
    with ThreadPoolExecutor(10) as ex: return list(ex.map(enrich, out))

def lane_repos(P):
    since = (datetime.now() - timedelta(days=P.get('repo_days', 14))).strftime('%Y-%m-%d'); hdr = gh_headers()
    kws = ['agent OR skills OR mcp OR claude OR codex OR llm', 'reverse-engineering OR "reverse engineering" OR decompile OR "voice cloning" OR text-to-speech OR "video generation"'] + \
          ['"%s"' % b for b in P.get('boost', [])[:0]]
    items, seen = [], set()
    for q in kws:
        try:
            j = json.loads(get('https://api.github.com/search/repositories?' + urllib.parse.urlencode({'q': f'({q}) created:>{since} stars:>{P.get("min_stars", 150)}', 'sort': 'stars', 'order': 'desc', 'per_page': 20}), hdr))
        except Exception: continue
        for r in j.get('items', []):
            if r['full_name'] not in seen: seen.add(r['full_name']); items.append(r)
    items.sort(key=lambda r: r['stargazers_count'], reverse=True)
    def enrich(a):
        idx, r = a; base = f"https://raw.githubusercontent.com/{r['full_name']}/HEAD/"; snip, img = '', ''
        if idx < 14:
            try:
                rd = get(f"https://api.github.com/repos/{r['full_name']}/readme", {**hdr, 'Accept': 'application/vnd.github.raw'}, 8).decode('utf-8', 'ignore')
                snip, img = readme_snip(rd), readme_image(rd, base)
            except Exception: pass
        desc = (r.get('description') or '').strip()
        chips = ([r['language']] if r.get('language') else []) + ['#' + t for t in (r.get('topics') or [])[:3]]
        return {'t': r['full_name'], 'u': r['html_url'], 's': 'GitHub', 'd': r['created_at'], 'b': (desc + ('\n' if desc and snip else '') + snip)[:420], 'c': chips,
                'st': ['★ %s' % kfmt(r['stargazers_count']), '⑂ %s' % kfmt(r['forks_count'])], 'stars': r['stargazers_count'],
                'raw_img': img or 'https://opengraph.githubassets.com/1/' + r['full_name']}
    with ThreadPoolExecutor(8) as ex: return list(ex.map(enrich, list(enumerate(items))[:MAXLANE]))

def lane_creator(P):
    since = int(time.time()) - 7 * 86400; bad = re.compile(r'uncensored|nsfw|porn|lora|abliterat', re.I)
    def hf(a):
        tag, lab = a
        try: j = json.loads(get(f'https://huggingface.co/api/models?pipeline_tag={tag}&sort=trendingScore&direction=-1&limit=12'))
        except Exception: return []
        out = []
        for r in j:
            if bad.search(r['id']) or r.get('likes', 0) < 40: continue
            snip, img = '', ''
            try:
                rd = get(f"https://huggingface.co/{r['id']}/raw/main/README.md", t=6).decode('utf-8', 'ignore')
                snip, img = readme_snip(rd), readme_image(rd, f"https://huggingface.co/{r['id']}/resolve/main/")
            except Exception: pass
            tags = [t for t in (r.get('tags') or []) if not re.match(r'^(region:|license:|diffusers|safetensors|endpoints|transformers|text-to|image-to|arxiv:|base_model|autotrain|onnx|gguf)', t)][:3]
            out.append({'t': r['id'], 'u': 'https://huggingface.co/' + r['id'], 's': 'Hugging Face', 'd': '', 'b': snip or 'Trending %s model on Hugging Face.' % lab.lower(), 'c': [lab] + tags,
                        'st': ['♥ %s' % kfmt(r.get('likes', 0))] + (['⬇ %s' % kfmt(r['downloads'])] if r.get('downloads') else []), 'trend': r.get('trendingScore', 0), 'raw_img': img})
            if len(out) >= 4: break
        return out
    with ThreadPoolExecutor(5) as ex:
        mods = [m for r in ex.map(hf, [('text-to-image', 'Image'), ('image-to-video', 'Video'), ('text-to-video', 'Video'), ('text-to-speech', 'Voice'), ('text-to-audio', 'Music')]) for m in r]
    def hn(q):
        try: return json.loads(get('https://hn.algolia.com/api/v1/search?' + urllib.parse.urlencode({'query': q, 'tags': 'story', 'numericFilters': f'created_at_i>{since},points>15', 'hitsPerPage': 4})))['hits']
        except Exception: return []
    kw = re.compile(r'video|image|sora|veo|midjourney|runway|comfy|eleven|voice|speech|music|diffusion|creator|canva|figma|design|animation|3d|photo|film', re.I)
    with ThreadPoolExecutor(8) as ex: hits = [h for r in ex.map(hn, ['sora', 'veo', 'midjourney', 'runway', 'comfyui', 'elevenlabs', 'higgsfield', 'video generation', 'image generation', 'text-to-video']) for h in r]
    seen, hnitems = set(), []
    for h in sorted(hits, key=lambda h: h.get('points', 0), reverse=True):
        if h['objectID'] in seen or not h.get('title') or not kw.search(h['title']): continue
        seen.add(h['objectID']); hnitems.append(h)
    def hni(h):
        u = h.get('url') or 'https://news.ycombinator.com/item?id=' + h['objectID']; m = meta(u) if h.get('url') else {'desc': '', 'img': ''}
        return {'t': h['title'][:120], 'u': u, 's': 'Hacker News', 'd': h['created_at'], 'b': m['desc'][:340] or 'Discussion on Hacker News.', 'c': ['Creator'], 'st': ['▲ %s' % h.get('points', 0), '💬 %s' % h.get('num_comments', 0)], 'raw_img': m['img'], 'hn': h.get('points', 0)}
    with ThreadPoolExecutor(8) as ex: hnl = list(ex.map(hni, hnitems[:10]))
    mods.sort(key=lambda m: m['trend'], reverse=True)
    return mods + hnl

def lane_releases(P):
    hdr = gh_headers(); repos = list(dict.fromkeys(P.get('releases_repos', [])))
    def one(r):
        try: j = json.loads(get(f'https://api.github.com/repos/{r}/releases/latest', hdr, 8))
        except Exception: return None
        notes = []
        for ln in (j.get('body') or '').splitlines():
            ln = re.sub(r'^[#>*\-\s`]+|[*`]', '', ln).strip(); ln = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', ln)
            ln = re.sub(r'\s+by @\S+ in\s+\S+|\s*https?://\S+', '', ln).strip()
            if len(ln) > 12 and '|' not in ln and not ln.lower().startswith(('patch changes', 'minor changes', 'major changes', 'what', 'full changelog', 'release', 'highlights', 'changelog', 'new contributors')): notes.append(ln[:130])
            if len(notes) == 3: break
        v = j.get('tag_name', ''); m = re.search(r'@([^@]+)$', v); v = m.group(1) if m else v.replace('rust-', '')
        return {'t': r if len(r.split('/')[1]) < 5 else r.split('/')[1], 'u': j.get('html_url'), 's': r.split('/')[0], 'd': j.get('published_at'), 'b': '', 'c': [v[:14]], 'notes': notes,
                'raw_img': 'https://opengraph.githubassets.com/1/' + r}
    with ThreadPoolExecutor(10) as ex: res = [r for r in ex.map(one, repos) if r and r['d']]
    return sorted(res, key=lambda x: x['d'], reverse=True)

# ------------------------------------------------------------------ scoring
def score(it, lane, P):
    txt = (it['t'] + ' ' + it.get('b', '')).lower(); d = parse_date(it.get('d')); hrs = ((datetime.now(timezone.utc) - d).total_seconds() / 3600) if d else 72
    s = 100 * math.exp(-max(hrs, 0) / 72)
    if lane == 'repos': s += math.log10(max(it.get('stars', 1), 1)) * 25
    if lane == 'creator': s += math.log10(max(it.get('trend', 1), 1)) * 20 + math.log10(max(it.get('hn', 1), 1)) * 12
    if lane == 'labs': s += {'Anthropic': 30, 'OpenAI': 25, 'DeepMind': 25, 'Hugging Face': 12}.get(it['s'], 0) + math.log10(max(it.get('hn', 1), 1)) * 15
    for b in P.get('boost', []):
        if b.lower() in txt: s += 25
    return round(s, 1)

def build():
    P = prefs(); L = P.get('lanes', {}); fns = {'labs': lane_labs, 'releases': lane_releases, 'launches': lane_launches, 'repos': lane_repos, 'creator': lane_creator}
    t0 = time.time(); HOSTS.clear()
    def timed(f):
        t = time.time()
        try: return f(P), None, int((time.time() - t) * 1000)
        except Exception as e: return [], f'{type(e).__name__}: {e}'[:160], int((time.time() - t) * 1000)
    with ThreadPoolExecutor(5) as ex: futs = {k: ex.submit(timed, f) for k, f in fns.items() if L.get(k, True)}
    lanes, health, mute = {}, {}, [m.lower() for m in P.get('mute', [])]
    for k, fut in futs.items():
        items, err, ms = fut.result()
        n_raw = len(items)
        items = [i for i in items if not any(m in (i['t'] + ' ' + i.get('b', '')).lower() for m in mute)]
        for i in items: i['u'] = safe_url(i.get('u')); i['score'] = score(i, k, P); i['id'] = hashlib.sha1((i['u'] or i['t']).encode()).hexdigest()[:10]
        items = [i for i in items if i['u']]                      # drop anything that isn't a clean http(s) link
        if k != 'releases': items.sort(key=lambda i: i['score'], reverse=True)
        lanes[k] = items[:MAXLANE]
        health[k] = {'n': len(lanes[k]), 'ms': ms, 'error': err or ('no items returned' if n_raw == 0 else '')}
    os.makedirs(IMG, exist_ok=True); allitems = [i for l in lanes.values() for i in l]
    with ThreadPoolExecutor(10) as ex: urls = list(ex.map(lambda i: cache_img(i.get('raw_img', '')), allitems))
    keep = set()
    for i, u in zip(allitems, urls):
        i['img'] = u; i.pop('raw_img', None)
        if u: keep.add(os.path.basename(u))
    for f in os.listdir(IMG):
        if f.endswith('.jpg') and f not in keep: os.remove(os.path.join(IMG, f))
    hosts = {h: v for h, v in HOSTS.items() if v['fail']}
    return {'updated': datetime.now().isoformat(), 'desk': P.get('desk_items', 10), 'counts': {k: len(v) for k, v in lanes.items()}, 'lanes': lanes,
            'health': {'lanes': health, 'failing_hosts': hosts, 'seconds': round(time.time() - t0, 1), 'github_token': 'Authorization' in gh_headers()}}

GOOGLE_PRODUCT_ICONS = {'mail.google.com': 'gmail_2020q4_48dp', 'calendar.google.com': 'calendar_2020q4_48dp', 'drive.google.com': 'drive_2020q4_48dp', 'docs.google.com': 'docs_2020q4_48dp',
                        'meet.google.com': 'meet_2020q4_48dp'}

def fetch_icons():
    """Download each app icon in apps.json (never shipped in the repo — fetched on your machine)."""
    try: cfg = json.load(open(APPS))
    except Exception:
        try: cfg = json.load(open(APPS.replace('apps.json', 'apps.example.json')))
        except Exception: return
    os.makedirs(os.path.join(HERE, 'icons'), exist_ok=True)
    for a in cfg.get('apps', []):
        name = a.get('icon') or urllib.parse.urlparse(a['url']).netloc; dst = os.path.join(HERE, 'icons', name + '.png')
        if os.path.exists(dst): continue
        urls = [a['icon_url']] if a.get('icon_url') else []
        if name in GOOGLE_PRODUCT_ICONS: urls.append(f'https://www.gstatic.com/images/branding/product/2x/{GOOGLE_PRODUCT_ICONS[name]}.png')
        urls.append(f'https://www.google.com/s2/favicons?domain={name}&sz=128')
        for u in urls:
            try:
                b = get(u, t=8)
                if b[:4] == b'\x89PNG': open(dst, 'wb').write(b); print('icon', name); break
            except Exception: continue
        else: print('no icon for', name)

def main():
    if '--fetch-icons' in sys.argv: fetch_icons(); return
    P = prefs(); force = '--force' in sys.argv
    try: age = time.time() - os.path.getmtime(FEED)
    except Exception: age = 1e12
    if not force and age < P.get('refresh_minutes', 15) * 60: return
    lock = FEED + '.lock'
    try:
        if time.time() - os.path.getmtime(lock) < 180: return
    except OSError: pass
    open(lock, 'w').write(str(os.getpid()))
    try: data = build()
    finally:
        try: os.remove(lock)
        except OSError: pass
    if any(data['lanes'].values()): json.dump(data, open(FEED + '.tmp', 'w')); os.replace(FEED + '.tmp', FEED)

if __name__ == '__main__': main()
