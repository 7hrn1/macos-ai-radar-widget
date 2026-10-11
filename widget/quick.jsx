import { run } from 'uebersicht';
const DIR = '__DIR__';          // filled in by install.sh
export const command = 'cat "' + DIR + '/apps.json" 2>/dev/null || cat "' + DIR + '/apps.example.json"';
export const refreshFrequency = 30000;
export const initialState = { output: '' };
export const updateState = (e, prev) => (e.type === 'UB/COMMAND_RAN' && !e.error && e.output && e.output !== prev.output ? { output: e.output } : prev);
export const className = `
  --u: clamp(0.9px, calc(0.0425vw + 0.386px), 1.3px);
  left: 28px; top: 18px; width: calc(300 * var(--u)); height: calc(62 * var(--u)); display: grid; grid-template-columns: repeat(5, 1fr); gap: calc(10 * var(--u)); align-content: center;
  @media (min-width: 1600px) { left: 4vw; }
  z-index: 20;                                /* always above the feed widget so the icons stay clickable */
  * { box-sizing: border-box; }
  .tile { position: relative; aspect-ratio: 1; cursor: pointer; display: flex; align-items: center; justify-content: center; border-radius: calc(12 * var(--u));
          transition: transform .16s ease; will-change: transform; }
  .plate { position: relative; width: 100%; height: 100%; border-radius: calc(12 * var(--u)); background: #fff; display: flex; align-items: center; justify-content: center; overflow: hidden;
           box-shadow: 0 calc(4 * var(--u)) calc(10 * var(--u)) rgba(0,0,0,.34), 0 0 0 1px rgba(255,255,255,0), 0 0 0 0 rgba(0,0,0,0); transition: box-shadow .16s ease; }
  .tile:hover { transform: translateY(-3px); }
  .tile:hover .plate { box-shadow: 0 calc(10 * var(--u)) calc(20 * var(--u)) rgba(0,0,0,.36), 0 0 0 1px rgba(255,255,255,.55), 0 0 0 calc(3 * var(--u)) var(--ring); }
  .tile:active { transform: translateY(-1px) scale(.97); }
  .plate i { width: 66%; height: 66%; background: center/contain no-repeat; }
  .plate.bare { background: none; } .plate.bare i { width: 100%; height: 100%; border-radius: calc(12 * var(--u)); }
`;
// --- safety: only plain http(s) links may be opened, and every shell argument is single-quoted ---
const sh = (s) => "'" + String(s).replace(/'/g, "'\\''") + "'";
const safeUrl = (u) => { try { const x = new URL(u); return x.protocol === 'http:' || x.protocol === 'https:' ? x.href : null; } catch (e) { return null; } };
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const openApp = (url, profile) => {
  const s = safeUrl(url); if (!s) return;
  const p = /^[\w .-]+$/.test(profile || '') ? profile : 'Default';
  run('if [ -x ' + sh(CHROME) + ' ]; then ' + sh(CHROME) + ' --profile-directory=' + sh(p) + ' ' + sh(s) + ' >/dev/null 2>&1 & else /usr/bin/open ' + sh(s) + '; fi');
};
const ring = (hex) => { const m = /^#?([0-9a-f]{6})$/i.exec(hex || ''); if (!m) return 'rgba(167,139,250,.55)'; const n = parseInt(m[1], 16); return 'rgba(' + (n >> 16) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',.5)'; };
export const render = ({ output }) => {
  let d = null; try { d = JSON.parse(output); } catch (e) {}
  if (!d) return <div />;
  return (
    <div style={{ display: 'contents' }}>
      {d.apps.map((a) => (
        <div key={a.name} className="tile" title={a.name} style={{ '--ring': ring(a.color) }} onClick={() => openApp(a.url, d.chrome_profile)}>
          <span className={'plate' + (a.plate === false ? ' bare' : '')}><i style={{ backgroundImage: 'url(/__WIDGET__/icons/' + encodeURIComponent(a.icon) + '.png)' }} /></span>
        </div>))}
    </div>
  );
};
