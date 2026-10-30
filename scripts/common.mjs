// Shared helpers for the Node pipeline scripts.
import {readFile, appendFile} from 'node:fs/promises';
import {existsSync, readFileSync} from 'node:fs';
import {resolve, join} from 'node:path';
import {spawn, spawnSync} from 'node:child_process';

export function args() {
  const a = process.argv.slice(2), o = {};
  for (let i = 0; i < a.length; i++) if (a[i].startsWith('--')) { const k = a[i].slice(2); o[k] = (a[i + 1] && !a[i + 1].startsWith('--')) ? a[++i] : true; }
  return o;
}
export async function loadProject(dir = '.') {
  const root = resolve(dir), project = JSON.parse(await readFile(join(root, 'project.json'), 'utf8'));
  const meta = existsSync(join(root, 'audio/voice_meta.json')) ? JSON.parse(await readFile(join(root, 'audio/voice_meta.json'), 'utf8')) : null;
  const words = existsSync(join(root, 'align/words.json')) ? JSON.parse(await readFile(join(root, 'align/words.json'), 'utf8')).words : [];
  const duration = project.duration || meta?.duration;
  if (!duration) throw Error('no duration: run make_voice.py first or set "duration" in project.json');
  return {root, project, meta, words, duration, fps: project.fps || 30, W: project.width || 1080, H: project.height || 1920};
}
export const note = (root, msg) => appendFile(join(root, 'PROGRESS.md'), `\n- ${new Date().toISOString()} ${msg}`);
export function memAvailableMB() {
  try { const m = readFileSync('/proc/meminfo', 'utf8').match(/MemAvailable:\s+(\d+)/); return m ? Math.round(+m[1] / 1024) : null; } catch { return null; }
}
export function run(cmd, argv) {
  return new Promise((ok, fail) => { const p = spawn(cmd, argv, {stdio: ['ignore', 'ignore', 'pipe']}); let err = '';
    p.stderr.on('data', x => err = (err + x).slice(-4000)); p.on('error', fail); p.on('close', c => c === 0 ? ok() : fail(Error(`${cmd} exit ${c}: ${err}`))); });
}
export function probe(file) {
  const p = spawnSync('ffprobe', ['-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,nb_read_frames,r_frame_rate', '-of', 'json', file], {encoding: 'utf8'});
  if (p.status !== 0) return null; try { return JSON.parse(p.stdout).streams?.[0] || null; } catch { return null; }
}
