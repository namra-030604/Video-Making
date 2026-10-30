// mslib.js - motion-studio helper library (plain script, attaches window.MS).
// Everything here is a pure function of its inputs (time t, seed). No Math.random, no clocks.
(function () {
  const MS = {};
  // ---------- math ----------
  MS.clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  MS.lerp = (a, b, k) => a + (b - a) * k;
  MS.inv = (a, b, x) => MS.clamp((x - a) / (b - a));           // 0..1 progress of x between a and b
  MS.range = (t, a, b, ease = (k) => k) => ease(MS.inv(a, b, t));
  MS.mix = (a, b, k) => a.map((v, i) => MS.lerp(v, b[i], k));
  // ---------- seeded randomness (never Math.random) ----------
  MS.rng = (seed) => { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
  MS.hash = (i, seed = 1) => { let h = (i * 374761393 + seed * 668265263) >>> 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
  MS.noise1 = (x, seed = 1) => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return MS.lerp(MS.hash(i, seed), MS.hash(i + 1, seed), u) * 2 - 1; };
  // ---------- easing (no linear robotic motion) ----------
  const E = MS.ease = {};
  E.inOutSine = (k) => -(Math.cos(Math.PI * k) - 1) / 2;
  E.inCubic = (k) => k * k * k;
  E.outCubic = (k) => 1 - Math.pow(1 - k, 3);
  E.inOutCubic = (k) => k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
  E.outQuint = (k) => 1 - Math.pow(1 - k, 5);
  E.inOutExpo = (k) => k === 0 ? 0 : k === 1 ? 1 : k < 0.5 ? Math.pow(2, 20 * k - 10) / 2 : (2 - Math.pow(2, -20 * k + 10)) / 2;
  E.outBack = (k, s = 1.70158) => 1 + (s + 1) * Math.pow(k - 1, 3) + s * Math.pow(k - 1, 2);
  E.outElastic = (k) => k === 0 ? 0 : k === 1 ? 1 : Math.pow(2, -10 * k) * Math.sin((k * 10 - 0.75) * (2 * Math.PI) / 3) + 1;
  E.outBounce = (k) => { const n = 7.5625, d = 2.75; if (k < 1 / d) return n * k * k; if (k < 2 / d) return n * (k -= 1.5 / d) * k + 0.75; if (k < 2.5 / d) return n * (k -= 2.25 / d) * k + 0.9375; return n * (k -= 2.625 / d) * k + 0.984375; };
  // damped spring 0 -> 1 ; dt = seconds since start
  MS.spring = (dt, freq = 2.2, damp = 0.35) => dt <= 0 ? 0 : 1 - Math.exp(-damp * 10 * dt) * Math.cos(freq * 2 * Math.PI * dt);
  // squash & stretch: returns [sx, sy] keeping volume, from a 0..1 impact amount (+ = stretch tall, - = squash)
  MS.squash = (amt) => { const s = 1 + amt; return [1 / Math.sqrt(Math.max(0.2, s)), s]; };
  // impact wobble after a hit at time th (squash then settle)
  MS.hitWobble = (t, th, strength = 0.25) => { const d = t - th; if (d < 0) return 0; return -strength * Math.exp(-7 * d) * Math.cos(d * 22); };
  // ---------- beat grid ----------
  MS.beatLen = (bpm) => 60 / bpm;
  MS.beatAt = (t, bpm) => t / MS.beatLen(bpm);
  MS.pulse = (t, bpm, decay = 8) => { const b = MS.beatAt(t, bpm); const f = b - Math.floor(b); return Math.exp(-decay * f * MS.beatLen(bpm)); };
  MS.activeBeat = (beats, t) => { let cur = beats[0]; for (const b of beats) if (b.t <= t) cur = b; return cur; };
  // ---------- drawing basics ----------
  MS.roundRect = (ctx, x, y, w, h, r) => { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); };
  MS.withT = (ctx, x, y, rot, sx, sy, fn) => { ctx.save(); ctx.translate(x, y); ctx.rotate(rot || 0); ctx.scale(sx ?? 1, sy ?? sx ?? 1); fn(); ctx.restore(); };
  MS.palettes = {
    warmNeutral: { bg: '#efe8dc', ink: '#1d1a16', muted: '#8a8073', accent: '#ff4d2e', neon: '#00e0a4', ui: '#fffaf2' },
    darkSkyNeon: { bg: '#070a1a', bg2: '#16123a', ink: '#f3f0ff', muted: '#8b8fb8', accent: '#ff2fb3', neon: '#3dfcff', ui: '#121633' },
    archival: { bg: '#141414', ink: '#f1ece2', muted: '#9a958c', accent: '#e8c547', neon: '#e8c547', ui: '#202020' },
    paper: { bg: '#e9e1cf', ink: '#201c18', muted: '#7c7266', accent: '#e63b2e', neon: '#2f6bff', ui: '#fbf7ee' },
  };
  // ---------- kinetic typography (mixed bold serif + sans) ----------
  // words: [{text, font:'serif'|'sans'|'mono', color, size}] laid out on one line, popped in one by one
  MS.FONTS = { serif: '"Instrument Serif", "DM Serif Display", "Playfair Display", serif', sans: '"Inter Tight", "Inter", "Space Grotesk", sans-serif', mono: '"JetBrains Mono", monospace', display: '"Bebas Neue", "Anton", sans-serif' };
  MS.fontStr = (w, size) => `${w.font === 'serif' ? 'italic 400' : w.font === 'display' ? '400' : '800'} ${size}px ${MS.FONTS[w.font || 'sans']}`;
  MS.kineticLine = (ctx, words, t, { x, y, size = 120, t0 = 0, stagger = 0.08, dur = 0.55, align = 'center', gap = 0.28, color = '#111' } = {}) => {
    ctx.save(); ctx.textBaseline = 'alphabetic';
    const widths = words.map((w) => { ctx.font = MS.fontStr(w, w.size || size); return ctx.measureText(w.text).width; });
    const total = widths.reduce((a, b) => a + b, 0) + gap * size * (words.length - 1);
    let cx = align === 'center' ? x - total / 2 : x;
    words.forEach((w, i) => {
      const k = MS.inv(t0 + i * stagger, t0 + i * stagger + dur, t);
      if (k > 0) {
        const s = MS.ease.outBack(k, 2.2), rise = (1 - MS.ease.outCubic(k)) * size * 0.6;
        ctx.save(); ctx.translate(cx + widths[i] / 2, y + rise); ctx.scale(0.6 + 0.4 * s, 0.6 + 0.4 * s); ctx.rotate((1 - k) * (i % 2 ? 0.08 : -0.08));
        ctx.font = MS.fontStr(w, w.size || size); ctx.fillStyle = w.color || color; ctx.textAlign = 'center'; ctx.globalAlpha = MS.clamp(k * 3);
        ctx.fillText(w.text, 0, 0); ctx.restore();
      }
      cx += widths[i] + gap * size;
    });
    ctx.restore();
  };
  // ---------- cursor that drives every change ----------
  // keys: [{t, x, y, click?:true}] ; returns {x,y,press} ; moves with eased arcs between keys
  MS.cursorAt = (keys, t) => {
    let a = keys[0], b = keys[keys.length - 1];
    for (let i = 0; i < keys.length - 1; i++) if (t >= keys[i].t && t <= keys[i + 1].t) { a = keys[i]; b = keys[i + 1]; break; }
    if (t < keys[0].t) b = a; if (t > keys[keys.length - 1].t) a = b;
    const k = a === b ? 1 : MS.ease.inOutCubic(MS.inv(a.t, b.t, t));
    const arc = Math.sin(k * Math.PI) * Math.min(80, Math.hypot(b.x - a.x, b.y - a.y) * 0.15);
    let press = 0; for (const c of keys) if (c.click) { const d = t - c.t; if (d > -0.06 && d < 0.18) press = Math.max(press, 1 - Math.abs(d - 0.03) / 0.15); }
    return { x: MS.lerp(a.x, b.x, k), y: MS.lerp(a.y, b.y, k) - arc, press: MS.clamp(press) };
  };
  MS.drawCursor = (ctx, c, { scale = 1.6, color = '#111', ring = '#ff4d2e', keys = [], t = 0 } = {}) => {
    for (const k of keys) if (k.click) { const d = t - k.t; if (d >= 0 && d < 0.5) { const p = MS.ease.outCubic(d / 0.5); ctx.save(); ctx.strokeStyle = ring; ctx.globalAlpha = 1 - p; ctx.lineWidth = 6 * (1 - p) + 1; ctx.beginPath(); ctx.arc(k.x, k.y, 10 + p * 60, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); } }
    const s = scale * (1 - 0.18 * c.press);
    ctx.save(); ctx.translate(c.x, c.y); ctx.scale(s, s);
    ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 8; ctx.shadowOffsetY = 3;
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 26); ctx.lineTo(7, 20); ctx.lineTo(12, 31); ctx.lineTo(17, 29); ctx.lineTo(12, 18); ctx.lineTo(21, 18); ctx.closePath();
    ctx.fillStyle = color; ctx.fill(); ctx.shadowColor = 'transparent'; ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke(); ctx.restore();
  };
  // ---------- offscreen helper ----------
  const bufs = {};
  MS.buf = (name, w, h) => { let c = bufs[name]; if (!c || c.width !== w || c.height !== h) { c = bufs[name] = document.createElement('canvas'); c.width = w; c.height = h; } const x = c.getContext('2d'); x.setTransform(1, 0, 0, 1, 0, 0); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1; x.filter = 'none'; x.clearRect(0, 0, w, h); return [c, x]; };
  // ---------- post FX ----------
  // film grain from a seeded noise tile; offset changes per frame index (deterministic)
  let grainTile = null;
  MS.grain = (ctx, t, { amount = 0.07, fps = 60, seed = 7 } = {}) => {
    if (!grainTile) { grainTile = document.createElement('canvas'); grainTile.width = grainTile.height = 256; const g = grainTile.getContext('2d'); const im = g.createImageData(256, 256); const r = MS.rng(seed); for (let i = 0; i < im.data.length; i += 4) { const v = r() * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; } g.putImageData(im, 0, 0); }
    const f = Math.floor(t * fps), W = ctx.canvas.width, H = ctx.canvas.height;
    ctx.save(); ctx.globalAlpha = amount; ctx.globalCompositeOperation = 'overlay';
    const ox = Math.floor(MS.hash(f, seed) * 256), oy = Math.floor(MS.hash(f, seed + 9) * 256);
    ctx.fillStyle = ctx.createPattern(grainTile, 'repeat'); ctx.translate(-ox, -oy); ctx.fillRect(ox, oy, W, H); ctx.restore();
  };
  // soft bloom: blurred bright copy screened on top
  MS.bloom = (ctx, { strength = 0.45, radius = 24, threshold = 'brightness(1.4) contrast(1.6)' } = {}) => {
    const W = ctx.canvas.width, H = ctx.canvas.height, [c, x] = MS.buf('bloom', W >> 1, H >> 1);
    x.filter = `${threshold} blur(${radius / 2}px)`; x.drawImage(ctx.canvas, 0, 0, W >> 1, H >> 1);
    ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha = strength; ctx.drawImage(c, 0, 0, W, H); ctx.restore();
  };
  // chromatic aberration: split RGB and offset R/B horizontally by px
  MS.chromatic = (ctx, px = 4) => {
    if (px < 0.5) return; const W = ctx.canvas.width, H = ctx.canvas.height;
    const [src, sx] = MS.buf('ca_src', W, H); sx.drawImage(ctx.canvas, 0, 0);
    const [ch, cx] = MS.buf('ca_ch', W, H);
    ctx.save(); ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); ctx.globalCompositeOperation = 'lighter';
    [['#f00', -px], ['#0f0', 0], ['#00f', px]].forEach(([col, dx]) => { cx.globalCompositeOperation = 'source-over'; cx.clearRect(0, 0, W, H); cx.drawImage(src, 0, 0); cx.globalCompositeOperation = 'multiply'; cx.fillStyle = col; cx.fillRect(0, 0, W, H); ctx.drawImage(ch, dx, 0); });
    ctx.restore();
  };
  // anamorphic light flare at (x,y)
  MS.flare = (ctx, x, y, { r = 260, intensity = 1, color = '255,210,150' } = {}) => {
    if (intensity <= 0) return; ctx.save(); ctx.globalCompositeOperation = 'screen';
    let g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(${color},${0.9 * intensity})`); g.addColorStop(0.25, `rgba(${color},${0.35 * intensity})`); g.addColorStop(1, `rgba(${color},0)`);
    ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
    g = ctx.createLinearGradient(x - r * 4, y, x + r * 4, y); g.addColorStop(0, `rgba(${color},0)`); g.addColorStop(0.5, `rgba(${color},${0.55 * intensity})`); g.addColorStop(1, `rgba(${color},0)`);
    ctx.fillStyle = g; ctx.fillRect(x - r * 4, y - 3, r * 8, 6); ctx.restore();
  };
  MS.vignette = (ctx, amount = 0.45) => { const W = ctx.canvas.width, H = ctx.canvas.height; const g = ctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.35, W / 2, H / 2, Math.max(W, H) * 0.75); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${amount})`); ctx.save(); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore(); };
  // archival black & white: grayscale + contrast + seeded flicker, scratches, dust
  MS.archival = (ctx, t, { fps = 24, seed = 3, flicker = 0.08, scratches = 3 } = {}) => {
    const W = ctx.canvas.width, H = ctx.canvas.height, f = Math.floor(t * fps), [c, x] = MS.buf('arch', W, H);
    x.filter = `grayscale(1) contrast(1.35) brightness(${1 + (MS.hash(f, seed) - 0.5) * flicker}) sepia(0.12)`; x.drawImage(ctx.canvas, 0, 0);
    ctx.save(); ctx.drawImage(c, 0, 0); ctx.strokeStyle = 'rgba(255,255,255,.35)';
    for (let i = 0; i < scratches; i++) { if (MS.hash(f * 7 + i, seed) < 0.5) continue; const sx = MS.hash(f * 13 + i, seed) * W; ctx.lineWidth = 1 + MS.hash(i, f) * 1.5; ctx.beginPath(); ctx.moveTo(sx, 0); ctx.lineTo(sx + (MS.hash(i, f + 1) - 0.5) * 30, H); ctx.stroke(); }
    ctx.fillStyle = 'rgba(0,0,0,.6)'; for (let i = 0; i < 12; i++) { const px = MS.hash(f * 31 + i, seed + 2) * W, py = MS.hash(f * 17 + i, seed + 5) * H; ctx.beginPath(); ctx.arc(px, py, MS.hash(i, f + 3) * 3, 0, Math.PI * 2); ctx.fill(); }
    ctx.restore(); MS.vignette(ctx, 0.55);
  };
  // ---------- split screen (animated) ----------
  // panels: array of draw(ctx, rect) ; k: 0..1 open progress ; vertical or horizontal
  MS.splitScreen = (ctx, panels, k, { vertical = true, gap = 12, gapColor = '#000', skew = 0 } = {}) => {
    const W = ctx.canvas.width, H = ctx.canvas.height, n = panels.length;
    panels.forEach((draw, i) => {
      const size = (vertical ? W : H) / n, off = (1 - MS.ease.outQuint(MS.clamp(k * 1.3 - i * 0.15))) * (i % 2 ? 1 : -1) * (vertical ? H : W);
      const r = vertical ? { x: i * size, y: off, w: size, h: H } : { x: off, y: i * size, w: W, h: size };
      ctx.save(); ctx.beginPath(); ctx.rect(r.x + (i ? gap / 2 : 0), r.y, r.w - (i && i < n - 1 ? gap : gap / 2 * (n > 1)), r.h); ctx.clip(); draw(ctx, r); ctx.restore();
    });
    ctx.save(); ctx.fillStyle = gapColor; for (let i = 1; i < n; i++) { const p = i * (vertical ? W : H) / n; vertical ? ctx.fillRect(p - gap / 2, 0, gap, H * MS.ease.outCubic(k)) : ctx.fillRect(0, p - gap / 2, W * MS.ease.outCubic(k), gap); } ctx.restore();
  };
  // ---------- paper collage / torn paper ----------
  MS.tornPath = (x, y, w, h, seed = 1, jag = 14) => {
    const p = new Path2D(), r = MS.rng(seed), step = 18;
    p.moveTo(x, y + r() * jag);
    for (let i = step; i <= w; i += step) p.lineTo(x + i, y + r() * jag);
    for (let i = step; i <= h; i += step) p.lineTo(x + w - r() * jag, y + i);
    for (let i = w - step; i >= 0; i -= step) p.lineTo(x + i, y + h - r() * jag);
    for (let i = h - step; i >= 0; i -= step) p.lineTo(x + r() * jag, y + i);
    p.closePath(); return p;
  };
  // draw a paper scrap that slaps in: k 0..1 ; content(ctx) draws inside the scrap (image, text...)
  MS.paperScrap = (ctx, { x, y, w, h, rot = 0, seed = 1, fill = '#fbf7ee', k = 1, content = null, shadow = true }) => {
    if (k <= 0) return; const e = MS.ease.outBack(MS.clamp(k), 1.6), drop = (1 - MS.ease.outCubic(MS.clamp(k))) * 220;
    ctx.save(); ctx.translate(x + w / 2, y + h / 2 - drop); ctx.rotate(rot + (1 - e) * 0.3); ctx.scale(0.7 + 0.3 * e, 0.7 + 0.3 * e); ctx.translate(-w / 2, -h / 2);
    const path = MS.tornPath(0, 0, w, h, seed);
    if (shadow) { ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 24; ctx.shadowOffsetX = 8; ctx.shadowOffsetY = 14; ctx.fillStyle = fill; ctx.fill(path); ctx.restore(); }
    ctx.fillStyle = fill; ctx.fill(path); if (content) { ctx.save(); ctx.clip(path); content(ctx, w, h); ctx.restore(); }
    ctx.restore();
  };
  // torn-paper wipe reveal: draws `next(ctx)` revealed behind a ragged moving edge with a paper lip + shadow
  MS.tearReveal = (ctx, k, next, { seed = 5, color = '#f6f0e2', vertical = false } = {}) => {
    const W = ctx.canvas.width, H = ctx.canvas.height, e = MS.ease.inOutCubic(MS.clamp(k)), edge = e * (W + 200) - 100, r = MS.rng(seed);
    const pts = []; for (let yy = 0; yy <= H + 20; yy += 22) pts.push([edge + (r() - 0.5) * 60, yy]);
    const clip = new Path2D(); clip.moveTo(-10, -10); pts.forEach(([a, b]) => clip.lineTo(a, b)); clip.lineTo(-10, H + 10); clip.closePath();
    ctx.save(); ctx.clip(clip); next(ctx); ctx.restore();
    ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.4)'; ctx.shadowBlur = 20; ctx.shadowOffsetX = 10; ctx.strokeStyle = color; ctx.lineWidth = 16; ctx.beginPath(); pts.forEach(([a, b], i) => i ? ctx.lineTo(a, b) : ctx.moveTo(a, b)); ctx.stroke(); ctx.restore();
  };
  // ---------- kaleidoscope clone / spin ----------
  MS.kaleidoscope = (ctx, src, { cx, cy, radius = 500, segments = 8, rot = 0, zoom = 1 } = {}) => {
    const ang = (Math.PI * 2) / segments;
    for (let i = 0; i < segments; i++) {
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot + i * ang); if (i % 2) ctx.scale(1, -1);
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.arc(0, 0, radius, -ang / 2, ang / 2); ctx.closePath(); ctx.clip();
      const sw = src.width * zoom, sh = src.height * zoom; ctx.drawImage(src, -sw * 0.1, -sh / 2, sw, sh); ctx.restore();
    }
  };
  // ---------- neon glow stroke/text ----------
  MS.neon = (ctx, fn, color = '#3dfcff', blur = 28) => { ctx.save(); ctx.shadowColor = color; for (const b of [blur, blur / 2.5]) { ctx.shadowBlur = b; fn(); } ctx.restore(); };
  // ---------- assets ----------
  MS.loadImage = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = async () => { try { await i.decode(); } catch (e) {} res(i); }; i.onerror = rej; i.src = src; });
  // video assets: seek an <video> element to t (await before drawing). Use for B-roll clips.
  MS.loadVideo = (src) => new Promise((res, rej) => { const v = document.createElement('video'); v.muted = true; v.preload = 'auto'; v.src = src; v.onloadeddata = () => res(v); v.onerror = rej; });
  MS.seekVideo = (v, t) => new Promise((res) => { const tt = Math.min(Math.max(0, t), (v.duration || 1) - 0.001); if (Math.abs(v.currentTime - tt) < 1e-4) return res(); v.onseeked = () => res(); v.currentTime = tt; });
  // Fonts installed by the pack's install.sh (OFL) are served by the renderer at /__vsp/fonts/. Missing fonts fall back silently.
  MS.loadPackFonts = async (list = [['Inter', 'Inter.ttf'], ['Caveat', 'Caveat.ttf']]) => {
    for (const [name, file] of list) { try { const f = new FontFace(name, `url(/__vsp/fonts/${file})`); await f.load(); document.fonts.add(f); } catch (e) { /* fallback font */ } }
    await document.fonts.ready;
  };
  MS.fontsReady = async (specs) => { for (const s of specs) await document.fonts.load(s); await document.fonts.ready; };
  window.MS = MS;
})();
