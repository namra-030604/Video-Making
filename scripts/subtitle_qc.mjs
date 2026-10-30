#!/usr/bin/env node
// subtitle_qc.mjs - checks karaoke subtitles against the aligned words.
//   node scripts/subtitle_qc.mjs --project DIR
// Requires the scene's renderFrame(t) to return {subtitleBoxes:[[x,y,w,h],...], activeWord, activeStart}.
// Checks: (1) every subtitle box stays inside the safe zone (project.subtitles.safe_top..safe_bottom as a fraction
// of height, and inside the width) sampled every 0.1 s; (2) each aligned word becomes the highlighted word within
// one frame of its aligned start (up to 60 words sampled evenly). Writes out/subtitle_qc.json. Exit 1 on failure.
import {writeFile, mkdir} from 'node:fs/promises';
import {join} from 'node:path';
import {launch} from '../lib/browser.mjs';
import {args, loadProject} from './common.mjs';

const A = args(), P = await loadProject(A.project || '.');
const {root, project, meta, words, duration, fps, W, H} = P;
const top = project.subtitles?.safe_top ?? 0.70, bottom = project.subtitles?.safe_bottom ?? 0.92, side = project.subtitles?.safe_side ?? 0.05;
const report = {safe_zone: {top, bottom, side}, safe_area: {samples: 0, violations: []}, words: {checked: 0, failures: []}};
const b = await launch({root, page: A.page || project.page || 'index.html', tag: 'subqc', initData: {project, words, meta}});
try {
  for (let t = 0; t < duration; t += 0.1) {
    const m = await b.meta(t); report.safe_area.samples++;
    for (const [x, y, w, h] of m.subtitleBoxes || [])
      if (x < W * side - 0.5 || x + w > W * (1 - side) + 0.5 || y < H * top - 0.5 || y + h > H * bottom + 0.5) report.safe_area.violations.push({t: +t.toFixed(2), box: [x, y, w, h].map(Math.round)});
  }
  const step = Math.max(1, Math.ceil(words.length / 60));
  for (let i = 0; i < words.length; i += step) {
    const w = words[i]; let first = null;
    for (let f = Math.max(0, Math.floor(w.start * fps) - 3); f <= Math.ceil(w.start * fps) + 3; f++) {
      const m = await b.meta(f / fps);
      if (m.activeWord === w.word && Math.abs((m.activeStart ?? -1) - w.start) < 1e-3) { first = f; break; }
    }
    report.words.checked++;
    const err = first === null ? null : Math.abs(first / fps - w.start);
    if (err === null || err > 1 / fps + 1e-3) report.words.failures.push({word: w.word, start: w.start, first_frame: first, error_s: err});
  }
} finally { await b.close(); }
await mkdir(join(root, 'out'), {recursive: true});
report.pass = !report.safe_area.violations.length && !report.words.failures.length && report.words.checked > 0;
await writeFile(join(root, 'out/subtitle_qc.json'), JSON.stringify(report, null, 2) + '\n');
console.log(`subtitle QC: ${report.safe_area.samples} safe-area samples, ${report.safe_area.violations.length} violations; ${report.words.checked} words checked, ${report.words.failures.length} timing failures -> ${report.pass ? 'PASS' : 'FAIL'}`);
process.exit(report.pass ? 0 : 1);
