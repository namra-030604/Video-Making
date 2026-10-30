#!/usr/bin/env node
// selftest.mjs - proves headless Chrome can load a page, load the pack fonts and render two different frames.
import {mkdtemp, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {launch, findChrome} from './browser.mjs';
const dir = await mkdtemp(join(tmpdir(), 'vsp-selftest-'));
await writeFile(join(dir, 'index.html'), `<!doctype html><canvas id="art" width="64" height="64"></canvas><script>
const g=document.getElementById('art').getContext('2d');
window.ready=(async()=>{try{const f=new FontFace('Inter','url(/__vsp/fonts/Inter.ttf)');await f.load();document.fonts.add(f);window.font='Inter'}catch{window.font='fallback'}})();
window.renderFrame=t=>{g.fillStyle='#000';g.fillRect(0,0,64,64);g.fillStyle='#f80';g.fillRect(t*40,10,20,20);g.font='20px Inter';g.fillText('Hi',4,60);return {font:window.font}};</script>`);
let b;
try {
  const exe = await findChrome();
  b = await launch({root: dir, tag: 'selftest'});
  const a = await b.png(0), c = await b.png(0.5), m = await b.meta(0);
  const ok = a.subarray(1, 4).toString() === 'PNG' && a.length > 200 && !a.equals(c);
  console.log(JSON.stringify({chrome: exe, url_scheme: b.url.split(':')[0], png_bytes: a.length, frames_differ: !a.equals(c), font: m.font, ok}));
  process.exitCode = ok ? 0 : 1;
} catch (e) { console.log(JSON.stringify({ok: false, error: String(e.message || e)})); process.exitCode = 1; }
finally { if (b) await b.close(); await rm(dir, {recursive: true, force: true}); }
