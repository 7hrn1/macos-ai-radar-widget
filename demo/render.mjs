// Deterministic demo renderer: drives the REAL widgets (feed/quick/strip) and the REAL "See all" page in headless Chrome,
// one frame at a time (animations are scrubbed, the cursor path is scripted), and writes numbered JPEG frames.
//   node render.mjs --site http://127.0.0.1:8890 --out ./.work/frames [--fps 10]
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const SITE = arg('site'), OUT = arg('out'), FPS = +arg('fps', 10);
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const W = 1440, H = 900, SPEED = 3;                       // carousel runs 3x faster than real life so a 25 s clip shows several slides
if (!SITE || !OUT) { console.error('usage: node render.mjs --site <url> --out <dir>'); process.exit(2); }
fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(OUT, { recursive: true });

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const ease = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const fade = (t, a, b, c, d) => (t < a || t > d ? 0 : t < b ? ease((t - a) / (b - a)) : t <= c ? 1 : ease(1 - (t - c) / (d - c)));   // 0→1 in [a,b], hold to c, 1→0 by d
const path_ = (pts, t) => {                                // cursor path: eased interpolation between keyframes {t,x,y}
  if (t <= pts[0].t) return pts[0]; if (t >= pts.at(-1).t) return pts.at(-1);
  const i = pts.findIndex((p) => p.t > t) - 1, a = pts[i], b = pts[i + 1], k = ease((t - a.t) / (b.t - a.t));
  return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k };
};

const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--hide-scrollbars', '--disable-gpu'] });
const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
let n = 0;
const shot = async (page, scene) => page.screenshot({ path: path.join(OUT, `${scene}_${String(n++).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 92 });

// ---------------------------------------------------------------- scene 1+2: the desktop (feed + shortcuts + markets), then the voice panel
const desk = await ctx.newPage();
await desk.goto(SITE + '/stage.html');
await desk.waitForSelector('body[data-ready]', { timeout: 30000 });
await desk.waitForLoadState('networkidle'); await desk.waitForTimeout(1200);
const center = (sel, i = 0) => desk.$$eval(sel, (els, i) => { const r = els[i].getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + Math.min(r.height / 2, 40) }; }, i);
const tiles = [await center('.tile', 3), await center('.tile', 1)];     // Gmail, then the 2nd shortcut
const heroTitle = await center('.card.hero .ttl');
const cursorPath = [
  { t: 0.0, x: 980, y: 760 }, { t: 1.6, x: 980, y: 760 }, { t: 3.4, ...tiles[0] }, { t: 5.0, ...tiles[0] }, { t: 5.9, ...tiles[1] }, { t: 7.0, ...tiles[1] },
  { t: 8.8, x: heroTitle.x, y: heroTitle.y + 60 }, { t: 10.8, x: heroTitle.x, y: heroTitle.y + 60 }, { t: 11.6, x: 1100, y: 800 },
];
const S1 = 11.5, S2 = 7.5;
const animT = (t) => 2000 + SPEED * (t - (clamp(t, 9.0, 10.8) - 9.0)) * 1000;   // time stands still while the cursor rests on a card (cards pause on hover)
const HUD = [['hud-listening.png', 0.0, 2.4], ['hud-working.png', 2.4, 4.6], ['hud-done.png', 4.6, 7.4]];

const apply = (page, f) => page.evaluate((f) => {
  document.getAnimations().forEach((a) => { if (a.animationName) { a.pause(); a.currentTime = f.anim; } });
  const cur = document.getElementById('cur'); cur.style.display = f.cur ? 'block' : 'none'; if (f.cur) { cur.style.left = f.cur.x + 'px'; cur.style.top = f.cur.y + 'px'; }
  const cap = document.getElementById('cap'); cap.textContent = f.cap || ''; cap.style.opacity = f.capO;
  const hud = document.getElementById('hud'); if (f.hud) { if (!hud.src.endsWith(f.hud)) hud.src = 'assets/' + f.hud; } hud.style.opacity = f.hudO;
  const key = document.getElementById('key'); key.style.opacity = f.keyO; key.style.transform = 'translateX(-50%) scale(' + (0.9 + 0.1 * f.keyO) + ')';
}, f);

const CAPS1 = [['Fresh AI news, agent repos & launches — right on your desktop', 0.2, 0.9, 3.4, 4.0], ['One-click shortcuts to the apps you live in', 4.2, 4.8, 7.4, 8.0], ['Cards keep sliding · hover one to pause', 8.2, 8.8, 10.8, 11.4]];
for (let i = 0, N = Math.round(S1 * FPS); i < N; i++) {
  const t = i / FPS, c = cursorPath.length ? path_(cursorPath, t) : null;
  const cap = CAPS1.find(([, a, , , d]) => t >= a && t <= d);
  await desk.mouse.move(c.x, c.y);
  await apply(desk, { anim: animT(t), cur: t >= 1.2 ? c : null, cap: cap && cap[0], capO: cap ? fade(t, cap[1], cap[2], cap[3], cap[4]) : 0, hud: null, hudO: 0, keyO: 0 });
  await shot(desk, 's1');
}
await desk.mouse.move(1100, 880);
for (let i = 0, N = Math.round(S2 * FPS); i < N; i++) {
  const t = i / FPS, tg = S1 + t, h = HUD.find(([, a, b]) => t >= a && t < b) || HUD.at(-1);
  const hudO = t < 7.0 ? fade(t, 0.0, 0.35, 99, 100) : ease(1 - (t - 7.0) / 0.5);
  await apply(desk, { anim: animT(tg), cur: null, cap: 'Hold ⌥ Space and just talk — it answers on screen and out loud', capO: fade(t, 0.2, 0.7, 6.4, 7.0),
    hud: h[0], hudO: clamp(hudO, 0, 1), keyO: t < 2.4 ? fade(t, 0.0, 0.25, 99, 100) : ease(1 - (t - 2.4) / 0.3) });
  await shot(desk, 's2');
}

// ---------------------------------------------------------------- scene 3: the full "See all" page (real radar.html) + end card
const page = await ctx.newPage();
await page.goto(SITE + '/ai-radar/radar.html?lane=all');
await page.waitForSelector('.card', { timeout: 30000 }); await page.waitForLoadState('networkidle'); await page.waitForTimeout(800);
const css = fs.readFileSync(new URL('./stage.html', import.meta.url), 'utf8').split('/* demo overlays */')[1].split('</style>')[0];
await page.evaluate((css) => {
  const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s);
  document.body.insertAdjacentHTML('beforeend', '<div id="cap"></div><div id="end"><h1>AI <em>Radar</em></h1><p>A macOS desktop widget for AI news, agent repos &amp; launches</p><code>github.com/7hrn1/macos-ai-radar-widget</code></div>');
}, css);
const QUERY = 'claude', S3 = 11.0;
const set = (f) => page.evaluate((f) => {
  window.scrollTo(0, f.y);
  const q = document.getElementById('q'); if (q.value !== f.q) { q.value = f.q; q.dispatchEvent(new Event('input')); }
  const cap = document.getElementById('cap'); cap.textContent = f.cap || ''; cap.style.opacity = f.capO; document.getElementById('end').style.opacity = f.endO;
}, f);
const CAPS3 = [['…or open everything: tabs, search, infinite scroll', 0.2, 0.8, 5.3, 5.9], ['Search everything instantly', 6.0, 6.6, 8.6, 9.2]];
const lastShots = n;
for (let i = 0, N = Math.round(S3 * FPS); i < N; i++) {
  const t = i / FPS;
  const y = t < 1.2 ? 0 : t < 3.6 ? 760 * ease((t - 1.2) / 2.4) : t < 4.8 ? 760 * (1 - ease((t - 3.6) / 1.2)) : 0;
  const typed = t < 6.4 ? 0 : Math.min(QUERY.length, Math.floor((t - 6.4) * 7));
  const cap = CAPS3.find(([, a, , , d]) => t >= a && t <= d);
  await set({ y, q: QUERY.slice(0, typed), cap: cap && cap[0], capO: cap ? fade(t, cap[1], cap[2], cap[3], cap[4]) : 0, endO: t < 8.6 ? 0 : ease((t - 8.6) / 0.8) });
  await shot(page, 's3');
}
await browser.close();
console.log(`rendered ${n} frames @ ${FPS} fps → ${OUT}`);
