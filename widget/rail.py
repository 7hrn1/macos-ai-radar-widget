#!/usr/bin/env python3
"""Fast data for the markets strip: tickers (Yahoo Finance's unofficial chart endpoint — best effort) + system meters."""
import json, os, ssl, subprocess, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CTX = ssl.create_default_context(cafile='/etc/ssl/cert.pem') if os.path.exists('/etc/ssl/cert.pem') else ssl.create_default_context()


def prefs():
    for name in ('prefs.json', 'prefs.example.json'):
        try: return json.load(open(os.path.join(HERE, name)))
        except Exception: continue
    return {}


def stock(sym):
    try:
        r = urllib.request.Request(f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=30m&range=1d', headers={'User-Agent': 'Mozilla/5.0'})
        j = json.loads(urllib.request.urlopen(r, timeout=6, context=CTX).read())['chart']['result'][0]
        p, c = j['meta']['regularMarketPrice'], j['meta']['chartPreviousClose']
        return {'s': sym, 'p': p, 'pct': (p - c) / c * 100 if c else 0, 'h': [x for x in j['indicators']['quote'][0]['close'] if x is not None]}
    except Exception:
        return None


def sysinfo():
    try: return json.loads(subprocess.run([os.path.join(HERE, 'system.sh')], capture_output=True, text=True, timeout=8).stdout)
    except Exception: return {}


if __name__ == '__main__':
    with ThreadPoolExecutor(10) as ex:
        futs = [ex.submit(stock, s) for s in prefs().get('tickers', ['NVDA', 'SPY'])]
        sy = ex.submit(sysinfo)
        print(json.dumps({'stocks': [f.result() for f in futs if f.result()], 'system': sy.result()}))
