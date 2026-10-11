import { run } from 'uebersicht';
const DIR = '__DIR__';          // filled in by install.sh
const PY = '__PYTHON__';
export const command = 'cd "' + DIR + '" && (' + PY + ' engine.py >/dev/null 2>&1 &) ; cat feed.json';
export const refreshFrequency = 30000;
export const initialState = { output: '', nav: {} };
export const updateState = (e, prev) => {
  if (e.type === 'UB/COMMAND_RAN') return e.error || !e.output || e.output === prev.output ? prev : { ...prev, output: e.output };
  if (e.type === 'GOTO') { const o = prev.nav[e.lane] || { k: 0 }; return { ...prev, nav: { ...prev.nav, [e.lane]: { idx: e.idx, k: o.k + 1 } } }; }
  return prev;
};

export const className = `
  --u: clamp(0.9px, calc(0.0425vw + 0.386px), 1.3px);
  left: 28px; right: 28px; top: 18px; bottom: 92px; display: grid; grid-template-rows: calc(62 * var(--u)) calc(56 * var(--u)) minmax(0, 1fr); gap: calc(12 * var(--u));
  @media (min-width: 1600px) { left: 4vw; right: 4vw; bottom: 40px; }
  color: #f3f5f9; font-family: -apple-system, "SF Pro Display", "Inter", sans-serif; -webkit-font-smoothing: antialiased;
  --bg: rgba(13,17,23,.94); --line: #2a303b; --mut: #8b95ab; --soft: #a8b3cf; --pur2: #a78bfa;
  * { box-sizing: border-box; }
  @media (prefers-reduced-motion: reduce) { .track, .dot { animation: none !important; } }
  .hd { display: flex; align-items: center; justify-content: space-between; padding: 0 calc(4 * var(--u)) 0 calc(322 * var(--u)); }
  .hd h1 { margin: 0; font-size: calc(30 * var(--u)); font-weight: 800; letter-spacing: -.02em; line-height: 1; filter: drop-shadow(0 calc(1 * var(--u)) calc(3 * var(--u)) rgba(0,0,0,.45)); }
  .hd h1 em { font-style: normal; background: linear-gradient(90deg, #ddd2ff, #f9d4ff); -webkit-background-clip: text; color: transparent; }
  .hd p { margin: calc(7 * var(--u)) 0 0; font-size: calc(12 * var(--u)); color: #eef1f8; font-weight: 600; text-shadow: 0 1px calc(3 * var(--u)) rgba(0,0,0,.55); }
  .chips { display: flex; align-items: center; gap: calc(8 * var(--u)); } .chip { font-size: calc(12 * var(--u)); font-weight: 700; padding: calc(7 * var(--u)) calc(13 * var(--u)); border-radius: calc(11 * var(--u)); background: var(--bg); border: 1px solid var(--line); color: var(--soft); cursor: pointer; }
  .chip.hint { border-style: dashed; color: #8b95ab; cursor: default; } .chip:hover { border-color: #a8b3cf; color: #fff; } .chip.on { background: linear-gradient(135deg, #a78bfa, #7c3aed); border-color: transparent; color: #fff; box-shadow: 0 calc(4 * var(--u)) calc(16 * var(--u)) rgba(124,58,237,.4); }
  .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); grid-template-rows: minmax(0, 1fr) minmax(0, 1fr); gap: calc(14 * var(--u)); min-height: 0; }
  .card { background: var(--bg); border: 1px solid var(--line); border-radius: calc(20 * var(--u)); padding: calc(16 * var(--u)) calc(18 * var(--u)); min-height: 0; overflow: hidden; box-shadow: 0 calc(10 * var(--u)) calc(30 * var(--u)) rgba(0,0,0,.35); display: flex; flex-direction: column; }
  .card.hero { grid-column: 1 / span 2; grid-row: 1 / span 2; padding: calc(20 * var(--u)) calc(22 * var(--u)); background: radial-gradient(120% 90% at 0% 0%, rgba(124,58,237,.28), transparent 55%), var(--bg); }
  .cap { display: flex; align-items: center; justify-content: space-between; gap: calc(8 * var(--u)); font-size: calc(11 * var(--u)); font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--mut); margin-bottom: calc(8 * var(--u)); flex: none; white-space: nowrap; }
  .cap > span { overflow: hidden; text-overflow: ellipsis; min-width: 0; } .cap > span .all { margin-left: calc(6 * var(--u)); } .ctl { display: flex; align-items: center; gap: calc(6 * var(--u)); }
  .dots { display: flex; gap: calc(4 * var(--u)); } .dot { width: calc(6 * var(--u)); height: calc(6 * var(--u)); border-radius: calc(6 * var(--u)); background: #394152; }
  .arw { width: calc(22 * var(--u)); height: calc(22 * var(--u)); line-height: calc(20 * var(--u)); text-align: center; border-radius: calc(8 * var(--u)); background: #1a1f29; border: 1px solid var(--line); color: var(--soft); font-size: calc(14 * var(--u)); cursor: pointer; letter-spacing: 0; }
  .arw:hover { background: #2a303b; color: #fff; } .all { font-size: calc(10.5 * var(--u)); letter-spacing: 0; text-transform: none; color: var(--pur2); cursor: pointer; font-weight: 700; } .all:hover { text-decoration: underline; }
  .vp { flex: 1; min-height: 0; overflow: hidden; border-radius: calc(12 * var(--u)); }
  .track { display: flex; height: 100%; animation-iteration-count: infinite; animation-timing-function: cubic-bezier(.65,0,.35,1); }
  .card:hover .track, .card:hover .dot { animation-play-state: paused; }
  .sl { height: 100%; padding-right: calc(2 * var(--u)); display: flex; flex-direction: column; cursor: pointer; min-width: 0; }
  .hero .sim { flex: 0 0 52%; max-height: none; min-height: calc(120 * var(--u)); margin-bottom: calc(14 * var(--u)); border-radius: calc(16 * var(--u)); }
  .sbody { flex: 1; min-width: 0; display: flex; flex-direction: column; min-height: 0; }
  .sm { display: flex; align-items: center; gap: calc(7 * var(--u)); font-size: calc(11.5 * var(--u)); color: var(--mut); font-weight: 600; white-space: nowrap; }
  .sm b { color: var(--pur2); font-weight: 700; } .new { background: #ff5c39; color: #fff; padding: calc(2 * var(--u)) calc(8 * var(--u)); border-radius: calc(7 * var(--u)); font-size: calc(10.5 * var(--u)); font-weight: 800; letter-spacing: .04em; }
  .ttl { font-size: calc(15 * var(--u)); font-weight: 800; line-height: 1.22; letter-spacing: -.01em; margin: calc(7 * var(--u)) 0 calc(5 * var(--u)); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; word-break: break-word; }
  .hero .ttl { font-size: clamp(calc(24 * var(--u)), 2.1vw, calc(36 * var(--u))); -webkit-line-clamp: 3; margin: calc(8 * var(--u)) 0 calc(8 * var(--u)); letter-spacing: -.02em; } .sl:hover .ttl { color: var(--pur2); } .sl:hover .ttl { color: var(--pur2); }
  .bd { flex: 1 1 0; min-height: calc(36 * var(--u)); overflow: hidden; font-size: calc(12 * var(--u)); line-height: 1.42; color: var(--soft); -webkit-mask-image: linear-gradient(#000 calc(100% - 22px), transparent); mask-image: linear-gradient(#000 calc(100% - 22px), transparent); }
  .hero .bd { font-size: calc(14.5 * var(--u)); line-height: 1.5; }
  .notes { margin: calc(6 * var(--u)) 0 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: calc(6 * var(--u)); flex: 1 1 0; min-height: calc(36 * var(--u)); overflow: hidden; -webkit-mask-image: linear-gradient(#000 calc(100% - 20px), transparent); mask-image: linear-gradient(#000 calc(100% - 20px), transparent); }
  .notes li { font-size: calc(12 * var(--u)); line-height: 1.38; color: var(--soft); padding-left: calc(14 * var(--u)); position: relative; flex: none; }
  .notes li::before { content: ''; position: absolute; left: 1px; top: calc(6 * var(--u)); width: calc(6 * var(--u)); height: calc(6 * var(--u)); border-radius: 50%; background: var(--pur2); }
  .ver { font-size: calc(11.5 * var(--u)); font-weight: 800; padding: calc(3 * var(--u)) calc(9 * var(--u)); border-radius: calc(8 * var(--u)); background: rgba(139,92,246,.28); color: #c4b5fd; }
  .tags { display: flex; gap: calc(6 * var(--u)); margin-top: auto; padding-top: calc(6 * var(--u)); overflow: hidden; flex-wrap: nowrap; }
  .tag { font-size: calc(10.5 * var(--u)); font-weight: 700; color: var(--soft); background: #1a1f29; border: 1px solid var(--line); padding: calc(2 * var(--u)) calc(8 * var(--u)); border-radius: calc(8 * var(--u)); white-space: nowrap; max-width: calc(104 * var(--u)); overflow: hidden; text-overflow: ellipsis; }
  .ft { display: flex; align-items: center; justify-content: space-between; margin-top: calc(6 * var(--u)); font-size: calc(11.5 * var(--u)); font-weight: 700; color: var(--soft); flex: none; }
  .ft .st { display: flex; gap: calc(12 * var(--u)); } .ft .st span { color: #fbbf24; } .ft .go { color: var(--mut); font-weight: 600; }
  .bmk { cursor: pointer; padding: calc(2 * var(--u)) calc(7 * var(--u)); border-radius: calc(8 * var(--u)); font-size: calc(13 * var(--u)); opacity: .55; } .bmk:hover { background: #2a303b; opacity: 1; }
  .sim { flex: 0 0 36%; min-height: calc(70 * var(--u)); max-height: calc(230 * var(--u)); border-radius: calc(12 * var(--u)); margin-bottom: calc(8 * var(--u)); background: #1a1f29 center/cover no-repeat; border: 1px solid var(--line); position: relative; overflow: hidden; }
  .sim.ph { background: linear-gradient(135deg, #2a2160, #17304a); display: flex; align-items: center; justify-content: center; font-size: calc(26 * var(--u)); font-weight: 800; color: rgba(255,255,255,.35); }
  .im { width: 36%; flex: none; border-radius: calc(14 * var(--u)); background: #1a1f29 center/cover no-repeat; border: 1px solid var(--line); }
  .im.ph { background: linear-gradient(135deg, #2a2160, #17304a); display: flex; align-items: center; justify-content: center; font-size: calc(44 * var(--u)); font-weight: 800; color: rgba(255,255,255,.3); }
`;

const START = Date.now();
const sick = (d) => { const l = (d.health && d.health.lanes) || {}, bad = Object.keys(l).filter((k) => l[k].error || l[k].n === 0).length; return bad ? ' · ⚠ ' + bad + ' source' + (bad > 1 ? 's' : '') + ' need attention (run: radar doctor)' : ''; };
const T = 9, TR = 0.5;
const enc = (it) => btoa(unescape(encodeURIComponent(JSON.stringify(it))));
// --- safety: only plain http(s) links may be opened, and every shell argument is single-quoted ---
const sh = (s) => "'" + String(s).replace(/'/g, "'\\''") + "'";
const safeUrl = (u) => { try { const x = new URL(u); return x.protocol === 'http:' || x.protocol === 'https:' ? x.href : null; } catch (e) { return null; } };
const openUrl = (u) => { const s = safeUrl(u); if (s) run('/usr/bin/open ' + sh(s)); };
const save = (it) => run(sh(PY) + ' ' + sh(DIR + '/save.py') + ' ' + sh(enc(it)));
const seeAll = (lane) => run('/usr/bin/open ' + sh('http://127.0.0.1:41416/__WIDGET__/radar.html?v=' + Date.now() + (lane && /^[a-z]+$/.test(lane) ? '&lane=' + lane : '')));   // ?v= defeats a stale cached copy
const ago = (iso) => { if (!iso) return ''; const h = Math.max(0, Math.round((Date.now() - new Date(iso)) / 36e5)); return h < 1 ? 'just now' : h < 24 ? h + 'h ago' : Math.round(h / 24) + 'd ago'; };
const keyframes = () => {
  let o = '';
  for (let n = 2; n <= 14; n++) {
    const p = 100 / n, tr = (TR / (n * T)) * 100, sh = 100 / (n + 1);
    o += '@keyframes car' + n + '{';
    for (let i = 0; i < n; i++) o += (i * p).toFixed(3) + '%{transform:translateX(-' + (i * sh).toFixed(3) + '%)}' + ((i + 1) * p - tr).toFixed(3) + '%{transform:translateX(-' + (i * sh).toFixed(3) + '%)}';
    o += '100%{transform:translateX(-' + (n * sh).toFixed(3) + '%)}}';
    o += '@keyframes dot' + n + '{0%{background:#a78bfa;width:16px}' + (p - 0.01).toFixed(3) + '%{background:#a78bfa;width:16px}' + p.toFixed(3) + '%,100%{background:#394152;width:6px}}';
  }
  return o;
};
const Slide = ({ it, hero, first }) => {
  const img = it.img ? 'url(' + it.img + ')' : null;
  return (
    <div className="sl" onClick={() => openUrl(it.u)}>
      {img ? <div className="sim" style={{ backgroundImage: img }} /> : <div className="sim ph">{(it.s || '?').slice(0, 1)}</div>}
      <div className="sbody">
        <div className="sm">{first && hero && <span className="new">NEW</span>}<b>{it.s}</b>{it.d && <span>· {ago(it.d)}</span>}</div>
        <div className="ttl">{it.t}</div>
        {it.notes && it.notes.length > 0 ? <ul className="notes">{it.notes.map((x, i) => <li key={i}>{x}</li>)}</ul> : <div className="bd">{it.b}</div>}
        {!it.notes && <div className="tags">{(it.c || []).slice(0, hero ? 4 : 3).map((c, i) => <span className="tag" key={i}>{c}</span>)}</div>}
        <div className="ft"><div className="st">{(it.st || []).map((x, i) => <span key={i}>{x}</span>)}{it.notes && <span className="ver">{(it.c || [''])[0]}</span>}</div>
          <div><span className="bmk" title="Save to cook later" onClick={(e) => { e.stopPropagation(); save({ n: it.t, u: it.u, d: (it.b || '').slice(0, 140) }); }}>🔖</span><span className="go">Open ↗</span></div></div>
      </div>
    </div>
  );
};
const Carousel = ({ lane, title, items, desk, hero, off, nav, dispatch }) => {
  let list = (items || []).slice(0, desk); if (list.length === 0) return <div className={'card' + (hero ? ' hero' : '')}><div className="cap"><span>{title}</span></div></div>;
  if (list.length < 2) list = list.concat(list);
  const n = Math.min(list.length, 14), pl = list.slice(0, n), all = pl.concat([pl[0]]);
  const st = nav[lane], k = st ? st.k : 0, delay = st ? -(st.idx * T) : -off;
  const go = (dir) => (e) => {
    e.stopPropagation();
    const track = e.currentTarget.closest('.card').querySelector('.track'), m = new DOMMatrix(getComputedStyle(track).transform), w = track.parentElement.clientWidth;
    const cur = Math.round(-m.m41 / w) % n; dispatch({ type: 'GOTO', lane, idx: (cur + dir + n) % n });
  };
  return (
    <div className={'card' + (hero ? ' hero' : '')}>
      <div className="cap"><span>{title} <span className="all" onClick={() => seeAll(lane)}>all ↗</span></span>
        <div className="ctl">{hero && <div className="dots">{pl.map((_, j) => <i key={j} className="dot" style={{ animationName: 'dot' + n, animationDuration: (n * T) + 's', animationIterationCount: 'infinite', animationDelay: (j * T + delay) + 's' }} />)}</div>}
          <span className="arw" onClick={go(-1)}>‹</span><span className="arw" onClick={go(1)}>›</span></div></div>
      <div className="vp"><div key={lane + k} className="track" style={{ width: ((n + 1) * 100) + '%', animationName: 'car' + n, animationDuration: (n * T) + 's', animationDelay: delay + 's' }}>
        {all.map((it, i) => <div key={i} style={{ width: (100 / (n + 1)) + '%', flex: 'none', height: '100%' }}><Slide it={it} hero={hero} first={i % n === 0} /></div>)}
      </div></div>
    </div>
  );
};
export const render = ({ output, nav }, dispatch) => {
  let d = null; try { d = JSON.parse(output); } catch (e) {}
  const L = (d && d.lanes) || {}, desk = (d && d.desk) || 10, total = d ? Object.values(d.counts || {}).reduce((a, b) => a + b, 0) : 0;
  return (
    <div style={{ display: 'contents' }}>
      <style>{keyframes()}</style>
      <div className="hd">
        <div><h1>AI <em>Radar</em></h1><p>{d ? total + ' items tracked · top ' + desk + ' per lane · updated ' + new Date(d.updated).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }) + sick(d) : 'Loading…'}</p></div>
        <div className="chips"><div className="chip hint">🎙 hold ⌥ Space</div><div className="chip on" onClick={() => seeAll('')}>For you</div><div className="chip" onClick={() => seeAll('labs')}>Labs</div><div className="chip" onClick={() => seeAll('repos')}>Agents</div><div className="chip" onClick={() => seeAll('creator')}>Creator</div></div>
      </div>
      <div />
      {!d ? <div className="card">Building your radar… (first run takes ~15s)</div> : (
        <div className="grid">
          <Carousel lane="labs" title="Labs & builders" items={L.labs} desk={desk} hero off={0} nav={nav} dispatch={dispatch} />
          <Carousel lane="releases" title="Fresh releases" items={L.releases} desk={desk} off={3.5} nav={nav} dispatch={dispatch} />
          <Carousel lane="launches" title="Launches" items={L.launches} desk={desk} off={5} nav={nav} dispatch={dispatch} />
          <Carousel lane="repos" title="Agents & skills" items={L.repos} desk={desk} off={7} nav={nav} dispatch={dispatch} />
          <Carousel lane="creator" title="Creator corner" items={L.creator} desk={desk} off={2} nav={nav} dispatch={dispatch} />
        </div>
      )}
    </div>
  );
};
