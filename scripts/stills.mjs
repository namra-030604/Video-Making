#!/usr/bin/env node
// stills.mjs - render review stills BEFORE the full render, plus a contact sheet and a blank/static scan.
//   node scripts/stills.mjs --project DIR [--times 0.5,2,4] [--n 6] [--scan] [--check]
//   --check: determinism test (each time rendered forward, then in reverse order, must give identical pixels;
//            no running CSS animations). Exits 1 on failure.
// Writes out/stills/still_NN.png, out/stills/contact.png (one row), out/stills/scan.json (with --scan).
import {mkdir, writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {launch} from '../lib/browser.mjs';
import {args, loadProject, run, note} from './common.mjs';

const A = args(), P = await loadProject(A.project || '.');
const {root, project, meta, words, duration} = P;
const n = +(A.n || 6);
const times = A.times ? String(A.times).split(',').map(Number) : Array.from({length: n}, (_, i) => +(duration * (i + 0.5) / n).toFixed(3));
const dir = join(root, 'out/stills'); await mkdir(dir, {recursive: true});
const b = await launch({root, page: A.page || project.page || 'index.html', tag: 'stills', initData: {project, words, meta}});
let checkFailed = false;
try {
  if (A.check) {
    // grab raw canvas pixels in the page after each seek; compare forward vs reverse order.
    // Tolerance: anti-aliasing / blur-filter jitter of a few gray levels is not a contract break, so a time passes
    // when no pixel differs by more than 8 levels (any larger change means state is carried between frames).
    const grab = (k) => `(()=>{const s=document.getElementById('art')||document.querySelector('canvas');const c=document.createElement('canvas');c.width=s.width;c.height=s.height;const q=c.getContext('2d');q.drawImage(s,0,0);(window.__vspSnap=window.__vspSnap||{})[${JSON.stringify(k)}]=q.getImageData(0,0,c.width,c.height).data;return 1})()`;
    for (const t of times) { await b.meta(t); await b.cdp.eval(grab('f' + t)); }
    for (const t of [...times].reverse()) { await b.meta(t); await b.cdp.eval(grab('r' + t)); }
    const res = [];
    for (const t of times) res.push({t, ...(await b.cdp.eval(`(()=>{const a=__vspSnap[${JSON.stringify('f' + t)}],b=__vspSnap[${JSON.stringify('r' + t)}];let m=0,big=0;for(let i=0;i<a.length;i++){const d=Math.abs(a[i]-b[i]);if(d>m)m=d;if(d>8)big++}return {max_delta:m,pixels_over_8:big}})()`))});
    const bad = res.filter(r => r.pixels_over_8 > 0).map(r => r.t), maxd = Math.max(...res.map(r => r.max_delta));
    const anims = await b.cdp.eval('document.getAnimations ? document.getAnimations().filter(a => a.playState === "running").length : 0');
    checkFailed = bad.length > 0 || anims > 0;
    console.log(`determinism check: ${times.length} times, ${bad.length} differ by > 8 levels${bad.length ? ' at ' + bad.join(',') : ''} (max delta ${maxd}); running CSS animations: ${anims} -> ${checkFailed ? 'FAIL' : 'PASS'}`);
  }
  for (let i = 0; i < times.length; i++) { await writeFile(join(dir, `still_${String(i + 1).padStart(2, '0')}.png`), await b.png(times[i])); console.log('still', i + 1, 't=' + times[i]); }
  if (A.scan) {
    const samples = [];
    for (let t = 0; t < duration; t += 0.25) {
      await b.meta(t);
      samples.push(await b.cdp.eval(`(()=>{const s=(document.getElementById('art')||document.querySelector('canvas'));const c=document.createElement('canvas');c.width=54;c.height=96;const q=c.getContext('2d');q.drawImage(s,0,0,54,96);const d=q.getImageData(0,0,54,96).data;let l=0,v=0;for(let i=0;i<d.length;i+=4){const y=.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];l+=y;v+=y*y}const N=d.length/4;l/=N;return {mean:l,variance:v/N-l*l,sig:c.toDataURL('image/jpeg',.5)}})()`).then(x => ({...x, t: +t.toFixed(2)})));
    }
    const out = samples.map((s, i) => ({t: s.t, mean: +s.mean.toFixed(1), variance: +s.variance.toFixed(1), identical_to_previous: i > 0 && s.sig === samples[i - 1].sig}));
    const report = {samples: out.length, near_blank: out.filter(s => s.mean < 8 || s.variance < 15).map(s => s.t), identical: out.filter(s => s.identical_to_previous).map(s => s.t)};
    await writeFile(join(dir, 'scan.json'), JSON.stringify({...report, per_sample: out}, null, 2) + '\n');
    console.log(`scan: ${report.samples} samples, ${report.near_blank.length} near-blank, ${report.identical.length} identical-to-previous`);
  }
} finally { await b.close(); }
await run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', join(dir, 'still_%02d.png'), '-vf', `scale=-2:480,tile=${times.length}x1:padding=8:margin=8:color=0x202020`, '-frames:v', '1', join(dir, 'contact.png')]);
await note(root, `stills: ${times.length} stills + contact sheet`);
console.log('contact sheet:', join(dir, 'contact.png'));
if (checkFailed) process.exit(1);
