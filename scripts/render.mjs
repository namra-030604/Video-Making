#!/usr/bin/env node
// render.mjs - restart-safe, frame-exact render: headless Chrome -> PNG frames -> ffmpeg, in small verified parts.
//
//   node scripts/render.mjs --project DIR [--page index.html] [--part-frames 150] [--threads 2] [--crf 18] [--out out/NAME.mp4]
//
// * The timeline is split into parts of N frames (project.render.part_frames, default 150 = 5 s at 30 fps).
// * Each part is encoded to out/parts/part_NNN.mp4 and verified (ffprobe frame count + size + fps) and stamped with
//   a hash of the sources. On re-run, valid parts are skipped, so a crash/restart only redoes the missing part.
// * Parts are rendered one at a time; before each part we check free memory (MemAvailable).
// * Then: concat (stream copy) -> mux audio/mix.wav (AAC 192k) -> optional small copy (<= 20 MB, project.render.small_height).
// * Every finished step is appended to PROGRESS.md.
import {mkdir, writeFile, stat, readdir} from 'node:fs/promises';
import {existsSync, readFileSync} from 'node:fs';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {join, resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {launch} from '../lib/browser.mjs';
import {args, loadProject, note, memAvailableMB, run, probe} from './common.mjs';

const A = args();
const P = await loadProject(A.project || '.');
const {root, project, meta, words, duration, fps, W, H} = P;
const page = A.page || project.page || 'index.html';
const PART = +(A['part-frames'] || project.render?.part_frames || 150);
const threads = String(A.threads || project.render?.threads || 2);
const crf = String(A.crf || project.render?.crf || 18);
const name = project.name || 'video';
const finalOut = resolve(root, A.out || project.output || `out/${name}.mp4`);
const total = Math.ceil(duration * fps);
const nParts = Math.ceil(total / PART);

// hash everything that changes pixels, so stale parts are re-rendered automatically
async function listFiles(dir) { const out = []; if (!existsSync(dir)) return out; for (const e of await readdir(dir, {withFileTypes: true})) { const p = join(dir, e.name); if (e.isDirectory()) out.push(...await listFiles(p)); else out.push(p); } return out; }
const hashInputs = [join(root, page), join(root, 'project.json')];
for (const d of project.render?.hash_dirs || ['scene']) hashInputs.push(...await listFiles(join(root, d)));
if (existsSync(join(root, 'align/words.json'))) hashInputs.push(join(root, 'align/words.json'));
const h = createHash('sha256'); for (const f of hashInputs.sort()) if (existsSync(f)) h.update(f.slice(root.length)).update(readFileSync(f));
const sourceHash = h.digest('hex').slice(0, 24);

const partFile = i => join(root, 'out/parts', `part_${String(i).padStart(3, '0')}.mp4`);
const partCount = i => Math.min(PART, total - i * PART);
function mediaOK(file, count) { const s = probe(file); return !!s && +s.nb_read_frames === count && +s.width === W && +s.height === H && s.r_frame_rate === `${fps}/1`; }
function partOK(i) { const f = partFile(i); if (!existsSync(f) || !existsSync(f + '.json')) return false; try { return JSON.parse(readFileSync(f + '.json', 'utf8')).sourceHash === sourceHash && mediaOK(f, partCount(i)); } catch { return false; } }

await mkdir(join(root, 'out/parts'), {recursive: true});
console.log(`render: ${total} frames @ ${fps} fps, ${W}x${H}, ${nParts} part(s) of <= ${PART} frames, source ${sourceHash}`);
const pending = [];
for (let i = 0; i < nParts; i++) { if (partOK(i)) console.log(`part ${i}: already valid, skipped`); else pending.push(i); }

if (pending.length) {
  const b = await launch({root, page, tag: 'render', initData: {project, words, meta}, width: W, height: H});
  try {
    const info = await b.info(); if (info.W !== W || info.H !== H) throw Error(`canvas is ${info.W}x${info.H}, project.json says ${W}x${H}`);
    for (const i of pending) {
      const mem = memAvailableMB();
      if (mem !== null && mem < 800) throw Error(`only ${mem} MB RAM available - stop your own idle processes and re-run (finished parts are kept)`);
      const count = partCount(i), file = partFile(i);
      const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-threads', threads, '-y', '-f', 'image2pipe', '-framerate', String(fps), '-vcodec', 'png', '-i', 'pipe:0',
        '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', crf, '-pix_fmt', 'yuv420p', '-r', String(fps), '-threads', threads, '-movflags', '+faststart', file], {stdio: ['pipe', 'ignore', 'pipe']});
      let err = ''; ff.stderr.on('data', x => err = (err + x).slice(-4000));
      try {
        for (let j = 0; j < count; j++) {
          const buf = await b.png((i * PART + j) / fps);
          if (!ff.stdin.write(buf)) await once(ff.stdin, 'drain');
        }
        ff.stdin.end(); const [code] = await once(ff, 'close'); if (code) throw Error('ffmpeg: ' + err);
      } catch (e) { ff.kill('SIGTERM'); throw e; }
      if (!mediaOK(file, count)) throw Error('part failed verification: ' + file);
      await writeFile(file + '.json', JSON.stringify({sourceHash, frames: count, width: W, height: H, fps}) + '\n');
      await note(root, `render: part ${i} verified (${count} frames)`); console.log(`part ${i}: rendered + verified (${count} frames)`);
    }
  } finally { await b.close(); }
}
for (let i = 0; i < nParts; i++) if (!partOK(i)) throw Error('invalid part ' + i);

const list = join(root, 'out/parts/concat.txt');
await writeFile(list, Array.from({length: nParts}, (_, i) => `file '${partFile(i)}'`).join('\n') + '\n');
const concat = join(root, 'out/parts/concat.mp4');
await run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', concat]);
await mkdir(resolve(finalOut, '..'), {recursive: true});
const mix = join(root, 'audio/mix.wav');
if (existsSync(mix)) {
  await run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-threads', threads, '-y', '-i', concat, '-i', mix, '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
    '-af', `apad,atrim=duration=${(total / fps).toFixed(4)}`, '-t', (total / fps).toFixed(4), '-movflags', '+faststart', finalOut]);
} else { console.log('WARNING: audio/mix.wav missing - rendering silent video'); await run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', concat, '-c', 'copy', '-movflags', '+faststart', finalOut]); }
await note(root, `render: final ${finalOut.slice(root.length + 1)}`);
console.log('final:', finalOut, (await stat(finalOut)).size, 'bytes');

const smallH = project.render?.small_height ?? (H > 1280 || W > 1280 ? 1280 : 0);
if (smallH && !A['no-small']) {
  const sh = Math.max(W, H) === H ? smallH : Math.round(smallH * H / W / 2) * 2, sw = Math.round(sh * W / H / 2) * 2;
  const small = finalOut.replace(/\.mp4$/, '-small.mp4');
  for (const q of [22, 24, 26, 28, 30]) {
    await run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-threads', threads, '-y', '-i', finalOut, '-vf', `scale=${sw}:${sh}:flags=lanczos`, '-c:v', 'libx264', '-profile:v', 'main', '-preset', 'medium', '-crf', String(q), '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', small]);
    if ((await stat(small)).size < 20e6) { await note(root, `render: small copy ${sw}x${sh} crf ${q}`); console.log('small:', small); break; }
  }
}
console.log('render complete');
