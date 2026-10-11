export const command = '__PYTHON__ "__DIR__/rail.py"';   // placeholders filled in by install.sh
export const refreshFrequency = 60000;
export const initialState = { output: '' };
export const updateState = (e, prev) => (e.type === 'UB/COMMAND_RAN' && !e.error && e.output && e.output !== prev.output ? { output: e.output } : prev);
export const className = `
  --u: clamp(0.9px, calc(0.0425vw + 0.386px), 1.3px);
  left: 28px; right: 28px; top: calc(18px + 74 * var(--u)); height: calc(56 * var(--u)); display: flex; gap: calc(8 * var(--u));
  @media (min-width: 1600px) { left: 4vw; right: 4vw; }
  color: #f3f5f9; font-family: -apple-system, "SF Pro Display", "Inter", sans-serif; -webkit-font-smoothing: antialiased;
  --bg: rgba(13,17,23,.94); --line: #2a303b; --mut: #8b95ab; --soft: #a8b3cf;
  * { box-sizing: border-box; }
  .tk, .sysc { background: var(--bg); border: 1px solid var(--line); border-radius: calc(15 * var(--u)); box-shadow: 0 calc(10 * var(--u)) calc(28 * var(--u)) rgba(0,0,0,.5), 0 calc(2 * var(--u)) calc(6 * var(--u)) rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.07); }
  .tk { flex: 1 1 0; min-width: 0; padding: 0 calc(12 * var(--u)); display: grid; grid-template-columns: 1fr auto; grid-template-rows: 1fr 1fr; align-items: center; column-gap: calc(8 * var(--u)); }
  .s { font-size: calc(12 * var(--u)); font-weight: 800; letter-spacing: .02em; align-self: end; }
  .pct { justify-self: end; align-self: end; font-size: calc(10.5 * var(--u)); font-weight: 800; padding: calc(2 * var(--u)) calc(7 * var(--u)); border-radius: calc(7 * var(--u)); font-variant-numeric: tabular-nums; }
  .p { font-size: calc(12 * var(--u)); color: #dfe4ee; font-variant-numeric: tabular-nums; align-self: start; white-space: nowrap; font-weight: 500; }
  .sp { width: calc(52 * var(--u)); height: calc(16 * var(--u)); justify-self: end; align-self: start; margin-top: calc(1 * var(--u)); }
  .up { background: rgba(52,211,153,.16); color: #34d399; } .dn { background: rgba(248,113,113,.16); color: #f87171; }
  .sysc { flex: 0 0 calc(230 * var(--u)); padding: calc(8 * var(--u)) calc(14 * var(--u)); display: grid; grid-template-columns: 1fr 1fr; gap: calc(7 * var(--u)) calc(14 * var(--u)); align-content: center; }
  .m .k { display: flex; justify-content: space-between; font-size: calc(9.5 * var(--u)); font-weight: 800; color: var(--mut); letter-spacing: .08em; margin-bottom: calc(3 * var(--u)); } .m .k span { color: var(--soft); }
  .tr { height: calc(3 * var(--u)); border-radius: 3px; background: #232833; overflow: hidden; } .fl { height: 100%; border-radius: 3px; }
`;
const Spark = ({ h, up }) => {
  if (!h || h.length < 2) return <svg className="sp" />;
  const mn = Math.min(...h), mx = Math.max(...h), r = mx - mn || 1;
  const pts = h.map((v, i) => (i / (h.length - 1) * 52).toFixed(1) + ',' + (14 - (v - mn) / r * 12).toFixed(1)).join(' ');
  return <svg className="sp" viewBox="0 0 52 16"><polyline points={pts} fill="none" stroke={up ? '#34d399' : '#f87171'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>;
};
const Meter = ({ k, v, c }) => (<div className="m"><div className="k">{k}<span>{v}%</span></div><div className="tr"><div className="fl" style={{ width: Math.min(v, 100) + '%', background: v > 85 ? '#f87171' : c }} /></div></div>);
export const render = ({ output }) => {
  let d = {}; try { d = JSON.parse(output); } catch (e) {}
  const sys = d.system || {};
  return (
    <div style={{ display: 'contents' }}>
      {(d.stocks || []).map((r) => (
        <div className="tk" key={r.s}>
          <span className="s">{r.s.replace('-USD', '')}</span>
          <span className={'pct ' + (r.pct >= 0 ? 'up' : 'dn')}>{r.pct >= 0 ? '+' : '−'}{Math.abs(r.pct).toFixed(2)}%</span>
          <span className="p">{r.p.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
          <Spark h={r.h} up={r.pct >= 0} />
        </div>))}
      <div className="sysc"><Meter k="CPU" v={sys.cpu || 0} c="#a78bfa" /><Meter k="MEM" v={sys.mem || 0} c="#38bdf8" /><Meter k="DISK" v={sys.disk || 0} c="#fbbf24" />{sys.bat != null ? <Meter k="BATT" v={sys.bat || 0} c="#34d399" /> : <div />}</div>
    </div>
  );
};
