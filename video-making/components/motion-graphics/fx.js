/* Canvas2D motion helpers. All animation state is derived from time and options. */
(function (root) {
  'use strict';
  const FX = {};
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const TAU = Math.PI * 2;
  const textPoints = new Map();
  const grainCache = new Map();
  const hash = (n) => { n = Math.imul(n ^ (n >>> 16), 0x7feb352d);
  n = Math.imul(n ^ (n >>> 15), 0x846ca68b);
  return (n ^ (n >>> 16)) >>> 0;
  };
  const mix = (a, b, k) => lerp(a, b, k * k * (3 - 2 * k));
  const rnd = (seed, n) => hash((seed | 0) + Math.imul(n | 0, 0x9e3779b9)) / 4294967296;
  const rect = (p) => Array.isArray(p) ? { x: p[0], y: p[1], w: p[2], h: p[3] } : p;
  const fontSpec = (size, font) => `${size}px ${font}`;
  function offscreen(w, h) {
    if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(w, h);
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    return c;
  }
  function pointsOf(path) {
    if (Array.isArray(path)) return path.map(p => Array.isArray(p) ? p : [p.x, p.y]);
    if (path && Array.isArray(path.points)) return pointsOf(path.points);
    throw new TypeError('path must be an array of [x,y] points or {points}');
  }
  function measure(points) {
    const lengths = [0];
    for (let i = 1; i < points.length; i++) lengths.push(lengths[i - 1] + Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]));
    return { lengths, total: lengths.at(-1) || 0 };
  }
  function trace(ctx, points, fraction = 1) {
    if (!points.length) return;
    const { lengths, total } = measure(points), limit = total * clamp(fraction);
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]);
    for (let i = 1; i < points.length; i++) {
      if (lengths[i] <= limit) ctx.lineTo(points[i][0], points[i][1]);
      else { const k = clamp((limit - lengths[i - 1]) / (lengths[i] - lengths[i - 1] || 1));
      ctx.lineTo(lerp(points[i - 1][0], points[i][0], k), lerp(points[i - 1][1], points[i][1], k));
      break;
      }
    }
  }
  /** Seeded mulberry32 generator. @param {number} seed=1 @returns {()=>number}
   * @default seed=1
   */
  FX.mulberry32 = function (seed = 1) {
    let a = seed | 0;
    return () => { a = (a + 0x6D2B79F5) | 0;
    let z = a;
    z = Math.imul(z ^ (z >>> 15), z | 1);
    z ^= z + Math.imul(z ^ (z >>> 7), z | 61);
    return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
    };
  };
  /** Smooth seeded value noise. @param {number} x @param {number} seed=1
   * @default seed=1
   */
  FX.noise1 = (x, seed = 1) => { const i = Math.floor(x);
  return mix(rnd(seed, i), rnd(seed, i + 1), x - i);
  };
  /** Smooth seeded 2D value noise. @param {number} x @param {number} y @param {number} seed=1
   * @default seed=1
   */
  FX.noise2 = (x, y, seed = 1) => { const ix = Math.floor(x), iy = Math.floor(y), kx = x - ix, ky = y - iy;
  const n = (a, b) => rnd(seed, hash(a ^ Math.imul(b, 65537)));
  return mix(mix(n(ix, iy), n(ix + 1, iy), kx), mix(n(ix, iy + 1), n(ix + 1, iy + 1), kx), ky);
  };
  /** Easing curves; inputs are normalized 0..1. outBack accepts optional overshoot s=1.70158.
   * @default outBack overshoot=1.70158
   */
  FX.ease = {
    linear: k => k,
    inSine: k => 1 - Math.cos(k * Math.PI / 2), outSine: k => Math.sin(k * Math.PI / 2),
    inOutSine: k => -(Math.cos(Math.PI * k) - 1) / 2,
    inQuad: k => k * k, outQuad: k => 1 - (1 - k) ** 2,
    inOutQuad: k => k < .5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2,
    inCubic: k => k ** 3, outCubic: k => 1 - (1 - k) ** 3,
    inOutCubic: k => k < .5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2,
    outQuint: k => 1 - (1 - k) ** 5,
    inOutExpo: k => k === 0 ? 0 : k === 1 ? 1 : k < .5 ? 2 ** (20 * k - 10) / 2 : (2 - 2 ** (-20 * k + 10)) / 2,
    outBack: (k, s = 1.70158) => 1 + (s + 1) * (k - 1) ** 3 + s * (k - 1) ** 2,
    outElastic: k => k === 0 || k === 1 ? k : 2 ** (-10 * k) * Math.sin((k * 10 - .75) * TAU / 3) + 1,
    outBounce: k => { const n = 7.5625, d = 2.75;
    if (k < 1 / d) return n * k * k;
    if (k < 2 / d) return n * (k -= 1.5 / d) * k + .75;
    if (k < 2.5 / d) return n * (k -= 2.25 / d) * k + .9375;
    return n * (k -= 2.625 / d) * k + .984375;
    }
  };
  /** Damped oscillator displacement. @param {number} dt elapsed seconds @param {number} freq=3 cycles/s @param {number} damp=5 decay/s
   * @default freq=3, damp=5
   */
  FX.spring = (dt, freq = 3, damp = 5) => 1 - Math.exp(-damp * Math.max(0, dt)) * Math.cos(TAU * freq * Math.max(0, dt));
  /** CSS-style cubic Bezier easing. @param {number} x1 @param {number} y1 @param {number} x2 @param {number} y2
   * @default none
   */
  FX.cubicBezier = (x1, y1, x2, y2) => k => { k = clamp(k);
  const b = (u, a, c) => 3 * (1 - u) ** 2 * u * a + 3 * (1 - u) * u * u * c + u ** 3;
  let lo = 0, hi = 1;
  for (let i = 0; i < 20; i++) { const m = (lo + hi) / 2;
  if (b(m, x1, x2) < k) lo = m;
  else hi = m;
  } return b((lo + hi) / 2, y1, y2);
  };
  /** Eased progress. @param {number} t seconds @param {number} a start @param {number} b end @param {Function} ease=FX.ease.inOutSine
   * @default ease=inOutSine
   */
  FX.prog = (t, a, b, ease = FX.ease.inOutSine) => ease(clamp((t - a) / (b - a || 1)));
  /** Staggered word entrance. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{words:string|string[],x:number,y:number,size?:number,font?:string,color?:string,t0?:number,stagger?:number,dur?:number,mode?:'pop'|'slide'|'drop'}} o
   * @default size=54, font=sans-serif, color=white, t0=0, stagger=.12, dur=.45, mode=pop
   */
  FX.kineticText = (ctx, t, o) => {
    const { words, x, y, size = 54, font = 'sans-serif', color = '#fff', t0 = 0, stagger = .12, dur = .45, mode = 'pop' } = o;
    const list = Array.isArray(words) ? words : String(words).split(/\s+/);
    ctx.save();
    ctx.font = `bold ${fontSpec(size, font)}`;
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = color;
    const widths = list.map(w => ctx.measureText(w).width), gap = size * .25, total = widths.reduce((a, b) => a + b, 0) + gap * (list.length - 1);
    let px = x - total / 2;
    list.forEach((w, i) => { const k = FX.prog(t, t0 + i * stagger, t0 + i * stagger + dur, FX.ease.outBack);
    if (t < t0 + i * stagger) { px += widths[i] + gap;
    return;
    } ctx.save();
    ctx.translate(px + widths[i] / 2, y);
    ctx.globalAlpha = clamp(k * 2);
    if (mode === 'slide') ctx.translate(-size * (1 - k), 0);
    if (mode === 'drop') ctx.translate(0, -size * (1 - k));
    if (mode === 'pop') ctx.scale(Math.max(.01, k), Math.max(.01, k));
    ctx.fillText(w, -widths[i] / 2, 0);
    ctx.restore();
    px += widths[i] + gap;
    });
    ctx.restore();
  };
  /** Reveal text through a moving rectangular mask. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{text:string,x:number,y:number,size?:number,font?:string,color?:string,t0?:number,dur?:number,direction?:'up'|'left'}} o
   * @default size=60, font=sans-serif, color=white, t0=0, dur=.7, direction=up
   */
  FX.textMaskReveal = (ctx, t, o) => {
    const { text, x, y, size = 60, font = 'sans-serif', color = '#fff', t0 = 0, dur = .7, direction = 'up' } = o;
    const k = FX.prog(t, t0, t0 + dur, FX.ease.outCubic);
    if (!k) return;
    ctx.save();
    ctx.font = `bold ${fontSpec(size, font)}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const w = ctx.measureText(text).width + size * .2, h = size * 1.4;
    ctx.beginPath();
    if (direction === 'left') ctx.rect(x - w / 2, y - h / 2, w * k, h);
    else ctx.rect(x - w / 2, y + h / 2 - h * k, w, h * k);
    ctx.clip();
    ctx.fillStyle = color;
    ctx.fillText(text, x, y);
    ctx.restore();
  };
  /** Seeded glyph particles from a cached text raster. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{text:string,x:number,y:number,size?:number,font?:string,color?:string,t0?:number,dur?:number,count?:number,seed?:number}} o
   * @default size=64, font=sans-serif, color=white, t0=0, dur=.8, count=350, seed=1
   */
  FX.particleText = (ctx, t, o) => {
    const { text, x, y, size = 64, font = 'sans-serif', color = '#fff', t0 = 0, dur = .8, count = 350, seed = 1 } = o;
    const key = `${text}|${size}|${font}`;
    if (!textPoints.has(key)) {
      const c = offscreen(Math.max(1, Math.ceil(text.length * size * .8 + size)), Math.ceil(size * 1.6));
      const g = c.getContext('2d');
      g.font = `bold ${fontSpec(size, font)}`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(text, c.width / 2, c.height / 2);
      const d = g.getImageData(0, 0, c.width, c.height).data, p = [];
      for (let yy = 0; yy < c.height; yy += 2) for (let xx = 0; xx < c.width; xx += 2) if (d[(yy * c.width + xx) * 4 + 3] > 128) p.push([xx - c.width / 2, yy - c.height / 2]);
      textPoints.set(key, p);
    }
    const pts = textPoints.get(key);
    if (!pts.length) return;
    ctx.save();
    ctx.fillStyle = color;
    for (let i = 0; i < count; i++) {
      const p = pts[Math.floor(rnd(seed, i * 3) * pts.length)], a = rnd(seed, i * 3 + 1) * TAU, r = size * (1.5 + rnd(seed, i * 3 + 2) * 3);
      const k = FX.prog(t, t0 + (i % 11) * .018, t0 + dur, FX.ease.outCubic);
      const px = x + lerp(Math.cos(a) * r, p[0], k), py = y + lerp(Math.sin(a) * r, p[1], k);
      ctx.globalAlpha = clamp(.2 + k);
      ctx.beginPath();
      ctx.arc(px, py, Math.max(1, size / 40), 0, TAU);
      ctx.fill();
    }
    ctx.restore();
  };
  /** Animated bars and counting labels. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{x:number,y:number,w:number,h:number,values:number[],labels?:string[],colors?:string[],t0?:number,stagger?:number,dur?:number,font?:string}} o
   * @default labels=[], colors=[cyan], t0=0, stagger=.12, dur=.7, font=sans-serif
   */
  FX.barChart = (ctx, t, o) => {
    const { x, y, w, h, values, labels = [], colors = ['#72e6d1'], t0 = 0, stagger = .12, dur = .7, font = 'sans-serif' } = o;
    const max = Math.max(1, ...values), slot = w / values.length, bw = slot * .56;
    ctx.save();
    ctx.font = `16px ${font}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    values.forEach((v, i) => { const k = FX.prog(t, t0 + i * stagger, t0 + i * stagger + dur, FX.ease.outCubic), bh = h * v / max * k, cx = x + slot * (i + .5);
    ctx.fillStyle = colors[i % colors.length];
    ctx.fillRect(cx - bw / 2, y + h - bh, bw, bh);
    ctx.fillStyle = '#fff';
    ctx.fillText(Math.round(v * k).toLocaleString('en-US'), cx, y + h - bh - 6);
    if (labels[i]) { ctx.textBaseline = 'top';
    ctx.fillText(labels[i], cx, y + h + 8);
    ctx.textBaseline = 'bottom';
    } });
    ctx.restore();
  };
  /** Progressive line with head marker. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{x:number,y:number,w:number,h:number,points:number[]|number[][],color?:string,t0?:number,dur?:number,lineWidth?:number}} o
   * @default color=cyan, t0=0, dur=1, lineWidth=4
   */
  FX.lineChart = (ctx, t, o) => {
    const { x, y, w, h, points, color = '#80f4de', t0 = 0, dur = 1, lineWidth = 4 } = o;
    const p = Array.isArray(points[0]) ? points.map(q => [x + q[0] * w, y + (1 - q[1]) * h]) : points.map((q, i) => [x + i * w / Math.max(1, points.length - 1), y + (1 - q) * h]);
    const k = FX.prog(t, t0, t0 + dur, FX.ease.inOutSine);
    if (p.length < 2 || !k) return;
    const { lengths, total } = measure(p), target = total * k;
    let head = p[0];
    for (let i = 1; i < p.length; i++) if (lengths[i] >= target) { const q = clamp((target - lengths[i - 1]) / (lengths[i] - lengths[i - 1] || 1));
    head = [lerp(p[i - 1][0], p[i][0], q), lerp(p[i - 1][1], p[i][1], q)];
    break;
    } else head = p[i];
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    trace(ctx, p, k);
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = 20;
    ctx.beginPath();
    ctx.arc(head[0], head[1], lineWidth * 2, 0, TAU);
    ctx.fill();
    ctx.restore();
  };
  /** Eased formatted number. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{from?:number,to:number,x:number,y:number,size?:number,font?:string,color?:string,t0?:number,dur?:number,decimals?:number,prefix?:string,suffix?:string}} o
   * @default from=0, size=72, font=sans-serif, color=white, t0=0, dur=1, decimals=0, prefix/suffix=empty
   */
  FX.counter = (ctx, t, o) => {
    const { from = 0, to, x, y, size = 72, font = 'sans-serif', color = '#fff', t0 = 0, dur = 1, decimals = 0, prefix = '', suffix = '' } = o;
    const v = lerp(from, to, FX.prog(t, t0, t0 + dur, FX.ease.outCubic));
    ctx.save();
    ctx.font = `bold ${fontSpec(size, font)}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = color;
    ctx.fillText(prefix + v.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + suffix, x, y);
    ctx.restore();
  };
  /** Frosted rise-in card; backdrop accepts a source canvas. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{x:number,y:number,w:number,h:number,r?:number,title?:string,body?:string,t0?:number,dur?:number,font?:string,tint?:string,backdrop?:HTMLCanvasElement}} o
   * @default r=22, title/body=empty, t0=0, dur=.65, font=sans-serif, tint=translucent white
   */
  FX.glassCard = (ctx, t, o) => {
    const { x, y, w, h, r = 22, title = '', body = '', t0 = 0, dur = .65, font = 'sans-serif', tint = 'rgba(255,255,255,.16)', backdrop } = o;
    const k = FX.prog(t, t0, t0 + dur, FX.ease.outCubic);
    if (!k) return;
    ctx.save();
    ctx.globalAlpha = k;
    ctx.translate(0, (1 - k) * 28);
    const path = () => { ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
    };
    if (backdrop) { ctx.save();
    path();
    ctx.clip();
    ctx.filter = 'blur(18px)';
    ctx.drawImage(backdrop, -22, -22, backdrop.width + 44, backdrop.height + 44);
    ctx.restore();
    }
    ctx.shadowColor = 'rgba(0,0,0,.3)';
    ctx.shadowBlur = 32;
    ctx.shadowOffsetY = 14;
    ctx.fillStyle = tint;
    path();
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;
    const grad = ctx.createLinearGradient(x, y, x + w, y + h);
    grad.addColorStop(0, 'rgba(255,255,255,.8)');
    grad.addColorStop(.6, 'rgba(255,255,255,.12)');
    grad.addColorStop(1, 'rgba(255,255,255,.35)');
    ctx.strokeStyle = grad;
    ctx.lineWidth = 2;
    path();
    ctx.stroke();
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.font = `bold 27px ${font}`;
    ctx.fillText(title, x + 25, y + 24, w - 50);
    ctx.font = `17px ${font}`;
    ctx.fillText(body, x + 25, y + 66, w - 50);
    ctx.restore();
  };
  /** Scene weights around a cut. @param {number} t @param {{cut:number,dur?:number}} o @returns {{a:number,b:number,k:number}}
   * @default dur=.3
   */
  FX.matchCut = (t, { cut, dur = .3 }) => { const k = FX.prog(t, cut - dur / 2, cut + dur / 2);
  return { a: 1 - k, b: k, k };
  };
  /** Interpolate matching scene rectangles. @param {number} k @param {object|number[]} fromRect @param {object|number[]} toRect
   * @default none
   */
  FX.matchTransform = (k, fromRect, toRect) => { const a = rect(fromRect), b = rect(toRect);
  return { x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), scale: lerp(b.w / (a.w || 1), b.h / (a.h || 1), .5) ** k };
  };
  /** Masked scene transition. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{type?:'wipe'|'circle'|'slide'|'dissolve'|'blinds',cut:number,dur?:number,drawA:Function,drawB:Function,W:number,H:number}} o
   * @default type=wipe, dur=.5
   */
  FX.transition = (ctx, t, o) => {
    const { type = 'wipe', cut, dur = .5, drawA, drawB, W, H } = o, k = FX.prog(t, cut, cut + dur, FX.ease.inOutCubic);
    if (k <= 0) { drawA(ctx);
    return;
    } if (k >= 1) { drawB(ctx);
    return;
    }
    ctx.save();
    drawA(ctx);
    ctx.restore();
    ctx.save();
    if (type === 'slide') { ctx.translate((1 - k) * W, 0);
    drawB(ctx);
    }
    else if (type === 'dissolve') { ctx.globalAlpha = k;
    drawB(ctx);
    }
    else { ctx.beginPath();
    if (type === 'circle') ctx.arc(W / 2, H / 2, Math.hypot(W, H) * k, 0, TAU);
    else if (type === 'blinds') { const n = 10;
    for (let i = 0; i < n; i++) ctx.rect(i * W / n, 0, W / n * k, H);
    } else ctx.rect(0, 0, W * k, H);
    ctx.clip();
    drawB(ctx);
    }
    ctx.restore();
  };
  /** RGB displacement and seeded horizontal slices from a source canvas. @param {CanvasRenderingContext2D} ctx @param {HTMLCanvasElement} source @param {number} t @param {{amount?:number,seed?:number,slices?:number}} o
   * @default amount=.5, seed=1, slices=14
   */
  FX.glitch = (ctx, source, t, { amount = .5, seed = 1, slices = 14 } = {}) => {
    amount = clamp(amount);
    const w = source.width, h = source.height, step = h / slices, tick = Math.floor(t * 24);
    ctx.save();
    ctx.drawImage(source, 0, 0);
    for (let i = 0; i < slices; i++) { const dx = (rnd(seed + tick, i) - .5) * 50 * amount;
    ctx.drawImage(source, 0, i * step, w, step, dx, i * step, w, step);
    }
    ctx.globalCompositeOperation = 'screen';
    ctx.globalAlpha = amount * .28;
    ctx.filter = 'sepia(1) saturate(8) hue-rotate(300deg)';
    ctx.drawImage(source, -8 * amount, 0);
    ctx.filter = 'sepia(1) saturate(8) hue-rotate(140deg)';
    ctx.drawImage(source, 8 * amount, 0);
    ctx.restore();
  };
  /** Dot-screen luminance rendering. @param {CanvasRenderingContext2D} ctx @param {HTMLCanvasElement} source @param {{x?:number,y?:number,w?:number,h?:number,cell?:number,angle?:number,color?:string,bg?:string}} o
   * @default x/y=0, w/h=source size, cell=8, angle=0, color=#111, bg=white
   */
  FX.halftone = (ctx, source, { x = 0, y = 0, w = source.width, h = source.height, cell = 8, angle = 0, color = '#111', bg = '#fff' } = {}) => {
    const sg = source.getContext('2d'), d = sg.getImageData(0, 0, source.width, source.height).data;
    ctx.save();
    ctx.fillStyle = bg;
    ctx.fillRect(x, y, w, h);
    ctx.translate(x + w / 2, y + h / 2);
    ctx.rotate(angle);
    ctx.fillStyle = color;
    const extent = Math.hypot(w, h) / 2;
    for (let py = -extent; py <= extent; py += cell) for (let px = -extent; px <= extent; px += cell) {
      const rx = px * Math.cos(angle) - py * Math.sin(angle) + w / 2, ry = px * Math.sin(angle) + py * Math.cos(angle) + h / 2;
      if (rx < 0 || rx >= w || ry < 0 || ry >= h) continue;
      const sx = Math.floor(rx / w * source.width), sy = Math.floor(ry / h * source.height), j = (sy * source.width + sx) * 4;
      const lum = (.2126 * d[j] + .7152 * d[j + 1] + .0722 * d[j + 2]) / 255, radius = Math.sqrt(1 - lum) * cell * .48;
      if (radius > .1) { ctx.beginPath();
      ctx.arc(px, py, radius, 0, TAU);
      ctx.fill();
      }
    }
    ctx.restore();
  };
  /** Apply camera transform inside caller save/restore. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{W:number,H:number,from:object,to:object,t0?:number,dur?:number,ease?:Function,shake?:object}} o @returns {object} camera state
   * @default t0=0, dur=1, ease=inOutSine, shake=null
   */
  FX.camera = (ctx, t, { W, H, from, to, t0 = 0, dur = 1, ease = FX.ease.inOutSine, shake = null }) => {
    const k = FX.prog(t, t0, t0 + dur, ease), cam = { x: lerp(from.x || 0, to.x || 0, k), y: lerp(from.y || 0, to.y || 0, k), zoom: lerp(from.zoom || 1, to.zoom || 1, k), rot: lerp(from.rot || 0, to.rot || 0, k) };
    ctx.translate(W / 2 + (shake?.x || 0), H / 2 + (shake?.y || 0));
    ctx.rotate(cam.rot + (shake?.rot || 0));
    ctx.scale(cam.zoom, cam.zoom);
    ctx.translate(-W / 2 - cam.x, -H / 2 - cam.y);
    return cam;
  };
  /** Layer offset for depth 0..1. @param {number} depth @param {object} cam
   * @default none
   */
  FX.parallax = (depth, cam) => ({ x: -(cam.x || 0) * clamp(depth), y: -(cam.y || 0) * clamp(depth) });
  /** Decaying deterministic camera shake. @param {number} t @param {{t0?:number,dur?:number,amp?:number,freq?:number,seed?:number}} o
   * @default t0=0, dur=.5, amp=12, freq=18, seed=1
   */
  FX.shake = (t, { t0 = 0, dur = .5, amp = 12, freq = 18, seed = 1 } = {}) => { const u = clamp((t - t0) / dur), a = t < t0 || t > t0 + dur ? 0 : amp * (1 - u) ** 2;
  return { x: a * (FX.noise1(t * freq, seed) * 2 - 1), y: a * (FX.noise1(t * freq, seed + 37) * 2 - 1), rot: a * .003 * (FX.noise1(t * freq, seed + 71) * 2 - 1) };
  };
  /** Draw first fraction of a point-list path with optional seeded wobble. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{path:number[][]|object,t0?:number,dur?:number,color?:string,width?:number,jitter?:number,seed?:number}} o
   * @default t0=0, dur=1, color=white, width=4, jitter=0, seed=1
   */
  FX.strokeDraw = (ctx, t, { path, t0 = 0, dur = 1, color = '#fff', width = 4, jitter = 0, seed = 1 }) => {
    const p = pointsOf(path).map(([x, y], i) => [x + (rnd(seed, i * 2) - .5) * jitter, y + (rnd(seed, i * 2 + 1) - .5) * jitter]);
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    trace(ctx, p, FX.prog(t, t0, t0 + dur, FX.ease.inOutSine));
    ctx.stroke();
    ctx.restore();
  };
  /** Blooming ink polygons. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{x:number,y:number,w:number,h:number,color?:string,seed?:number,spread?:number,t0?:number,dur?:number}} o
   * @default color=red, seed=1, spread=1, t0=0, dur=.8
   */
  FX.inkWash = (ctx, t, { x, y, w, h, color = '#e87b71', seed = 1, spread = 1, t0 = 0, dur = .8 }) => {
    const k = FX.prog(t, t0, t0 + dur, FX.ease.outCubic);
    if (!k) return;
    ctx.save();
    for (let layer = 5; layer >= 0; layer--) { const radius = k * spread * (1 + layer * .045);
    ctx.beginPath();
    for (let i = 0; i <= 40; i++) { const a = i / 40 * TAU, n = .77 + FX.noise2(Math.cos(a) * 3 + layer, Math.sin(a) * 3, seed) * .4, px = x + Math.cos(a) * w * .5 * radius * n, py = y + Math.sin(a) * h * .5 * radius * n;
    if (i) ctx.lineTo(px, py);
    else ctx.moveTo(px, py);
    } ctx.closePath();
    ctx.globalAlpha = layer === 0 ? .14 : .08;
    ctx.fillStyle = color;
    ctx.fill();
    }
    ctx.restore();
  };
  /** Cached deterministic paper grain overlay. @param {CanvasRenderingContext2D} ctx @param {{W:number,H:number,seed?:number,strength?:number}} o
   * @default seed=1, strength=.1
   */
  FX.paperGrain = (ctx, { W, H, seed = 1, strength = .1 }) => {
    const key = `${W}|${H}|${seed}`, scale = Math.max(1, Math.ceil(Math.max(W, H) / 700));
    if (!grainCache.has(key)) { const c = offscreen(Math.ceil(W / scale), Math.ceil(H / scale)), g = c.getContext('2d'), im = g.createImageData(c.width, c.height);
    for (let i = 0; i < im.data.length; i += 4) { const v = rnd(seed, i / 4) * 255;
    im.data[i] = im.data[i + 1] = im.data[i + 2] = v;
    im.data[i + 3] = 255;
    } g.putImageData(im, 0, 0);
    grainCache.set(key, c);
    }
    ctx.save();
    ctx.globalAlpha = clamp(strength);
    ctx.globalCompositeOperation = 'overlay';
    ctx.drawImage(grainCache.get(key), 0, 0, W, H);
    ctx.restore();
  };
  function resample(p, n) { const { lengths, total } = measure(p.concat([p[0]])), q = p.concat([p[0]]), out = [];
  for (let j = 0; j < n; j++) { const d = total * j / n;
  let i = 1;
  while (i < lengths.length - 1 && lengths[i] < d) i++;
  const k = (d - lengths[i - 1]) / (lengths[i] - lengths[i - 1] || 1);
  out.push([lerp(q[i - 1][0], q[i][0], k), lerp(q[i - 1][1], q[i][1], k)]);
  } return out;
  }
  /** Regular polygon point list. @param {number} cx @param {number} cy @param {number} r @param {number} n @param {number} rot=-PI/2
   * @default rot=-PI/2
   */
  FX.regularPolygon = (cx, cy, r, n, rot = -Math.PI / 2) => Array.from({ length: n }, (_, i) => [cx + r * Math.cos(rot + TAU * i / n), cy + r * Math.sin(rot + TAU * i / n)]);
  /** Star polygon point list. @param {number} cx @param {number} cy @param {number} r1 outer @param {number} r2 inner @param {number} n points
   * @default none
   */
  FX.star = (cx, cy, r1, r2, n) => Array.from({ length: n * 2 }, (_, i) => { const a = -Math.PI / 2 + Math.PI * i / n, r = i % 2 ? r2 : r1;
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  });
  /** Resampled polygon morph. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{shapeA:number[][],shapeB:number[][],t0?:number,dur?:number,ease?:Function,fill?:string}} o
   * @default t0=0, dur=1, ease=inOutSine, fill=white
   */
  FX.morph = (ctx, t, { shapeA, shapeB, t0 = 0, dur = 1, ease = FX.ease.inOutSine, fill = '#fff' }) => {
    const n = Math.max(shapeA.length, shapeB.length, 24), a = resample(pointsOf(shapeA), n), b = resample(pointsOf(shapeB), n), k = FX.prog(t, t0, t0 + dur, ease);
    ctx.save();
    ctx.fillStyle = fill;
    ctx.beginPath();
    for (let i = 0; i < n; i++) { const x = lerp(a[i][0], b[i][0], k), y = lerp(a[i][1], b[i][1], k);
    if (i) ctx.lineTo(x, y);
    else ctx.moveTo(x, y);
    } ctx.closePath();
    ctx.fill();
    ctx.restore();
  };
  /** Glow via additive shadow passes. @param {CanvasRenderingContext2D} ctx @param {Function} drawFn receives ctx @param {{color?:string,blur?:number,passes?:number}} o
   * @default color=cyan, blur=22, passes=3
   */
  FX.glow = (ctx, drawFn, { color = '#70f8ff', blur = 22, passes = 3 } = {}) => { ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.shadowColor = color;
  for (let i = passes; i > 0; i--) { ctx.shadowBlur = blur * i / passes;
  ctx.globalAlpha = 1 / (i + 1);
  drawFn(ctx);
  } ctx.restore();
  drawFn(ctx);
  };
  /** Moving specular band. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{x:number,y:number,w:number,h:number,t0?:number,dur?:number,angle?:number}} o
   * @default t0=0, dur=.8, angle=-.3
   */
  FX.lightSweep = (ctx, t, { x, y, w, h, t0 = 0, dur = .8, angle = -.3 }) => { const k = FX.prog(t, t0, t0 + dur, FX.ease.inOutSine);
  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();
  ctx.translate(x + w * k, y + h / 2);
  ctx.rotate(angle);
  const g = ctx.createLinearGradient(-w * .2, 0, w * .2, 0);
  g.addColorStop(0, 'rgba(255,255,255,0)');
  g.addColorStop(.5, 'rgba(255,255,255,.45)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(-w * .2, -h, w * .4, h * 2);
  ctx.restore();
  };
  /** Animated route on projected map coordinates. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{points:number[][],t0?:number,dur?:number,color?:string,dash?:number[]}} o
   * @default t0=0, dur=1, color=cyan, dash=[]
   */
  FX.mapRoute = (ctx, t, { points, t0 = 0, dur = 1, color = '#80f5db', dash = [] }) => {
    const p = pointsOf(points), k = FX.prog(t, t0, t0 + dur, FX.ease.inOutSine);
    if (p.length < 2 || !k) return;
    const { lengths, total } = measure(p), d = total * k;
    let head = p[0];
    for (let i = 1; i < p.length; i++) if (lengths[i] >= d) { const q = clamp((d - lengths[i - 1]) / (lengths[i] - lengths[i - 1] || 1));
    head = [lerp(p[i - 1][0], p[i][0], q), lerp(p[i - 1][1], p[i][1], q)];
    break;
    } else head = p[i];
    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.setLineDash(dash);
    trace(ctx, p, k);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.arc(head[0], head[1], 8, 0, TAU);
    ctx.fill();
    if (k > .95) { ctx.globalAlpha = (k - .95) * 10;
    ctx.beginPath();
    ctx.arc(p.at(-1)[0], p.at(-1)[1], 14 + 12 * Math.sin(t * TAU * 2) ** 2, 0, TAU);
    ctx.stroke();
    } ctx.restore();
  };
  /** Ordered timeline axis and event ticks. @param {CanvasRenderingContext2D} ctx @param {number} t @param {{x:number,y:number,w:number,events:{label:string,at:number}[],t0?:number,dur?:number,font?:string,color?:string}} o
   * @default t0=0, dur=1, font=sans-serif, color=white
   */
  FX.timeline = (ctx, t, { x, y, w, events, t0 = 0, dur = 1, font = 'sans-serif', color = '#fff' }) => {
    const k = FX.prog(t, t0, t0 + dur, FX.ease.inOutSine);
    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + w * k, y);
    ctx.stroke();
    ctx.font = `15px ${font}`;
    ctx.textAlign = 'center';
    events.forEach(e => { const p = clamp(e.at), ek = FX.prog(k, p, Math.min(1, p + .1), FX.ease.outBack);
    if (k < p) return;
    const ex = x + w * p;
    ctx.beginPath();
    ctx.moveTo(ex, y);
    ctx.lineTo(ex, y - 20 * ek);
    ctx.stroke();
    ctx.globalAlpha = clamp(ek);
    ctx.fillText(e.label, ex, y - 29);
    ctx.globalAlpha = 1;
    });
    ctx.restore();
  };
  /** Radial edge darkening. @param {CanvasRenderingContext2D} ctx @param {number} W @param {number} H @param {number} strength=.35
   * @default strength=.35
   */
  FX.vignette = (ctx, W, H, strength = .35) => { const g = ctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * .15, W / 2, H / 2, Math.hypot(W, H) * .6);
  g.addColorStop(0, 'rgba(0,0,0,0)');
  g.addColorStop(1, `rgba(0,0,0,${clamp(strength)})`);
  ctx.save();
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
  };
  root.FX = FX;
})(window);
