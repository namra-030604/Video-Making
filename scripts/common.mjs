// Shared helpers for the Node pipeline scripts.
import {readFile, appendFile} from 'node:fs/promises';
import {existsSync, readFileSync} from 'node:fs';
import {resolve, join, delimiter, win32, posix, dirname} from 'node:path';
import {freemem, platform, arch} from 'node:os';
import {fileURLToPath} from 'node:url';
import {spawn, spawnSync} from 'node:child_process';

export function args() {
  const a = process.argv.slice(2), o = {};
  for (let i = 0; i < a.length; i++) if (a[i].startsWith('--')) { const k = a[i].slice(2); o[k] = (a[i + 1] && !a[i + 1].startsWith('--')) ? a[++i] : true; }
  return o;
}
export async function loadProject(dir = '.') {
  requireVideoTier();
  const root = resolve(dir), project = JSON.parse(await readFile(join(root, 'project.json'), 'utf8'));
  const meta = existsSync(join(root, 'audio/voice_meta.json')) ? JSON.parse(await readFile(join(root, 'audio/voice_meta.json'), 'utf8')) : null;
  const words = existsSync(join(root, 'align/words.json')) ? JSON.parse(await readFile(join(root, 'align/words.json'), 'utf8')).words : [];
  const duration = project.duration || meta?.duration;
  if (!duration) throw Error('no duration: run make_voice.py first or set "duration" in project.json');
  return {root, project, meta, words, duration, fps: project.fps || 30, W: project.width || 1080, H: project.height || 1920};
}
export function requireVideoTier() {
  const state = join(dirname(fileURLToPath(import.meta.url)), '..', '.vsp-state', 'tier');
  if (process.env.VSP_VOICE_ONLY === '1' || (platform() === 'darwin' && arch() === 'x64') ||
      (existsSync(state) && readFileSync(state, 'utf8').trim() === 'voice-only')) {
    throw Error('Voice-only mode: Intel Macs and --voice-only installs do not have the pinned Torch/onnxruntime video stack or a supported Chrome rendering path. Video build, smoke, stills and render are disabled. Use vsp.py voice <project>, vsp.py audio <project>, or scripts/make_voice.py; see the docs.');
  }
}
export const note = (root, msg) => appendFile(join(root, 'PROGRESS.md'), `\n- ${new Date().toISOString()} ${msg}`);
export function toolPath(name, env = process.env, os = platform()) {
  const key = {ffmpeg:'VSP_FFMPEG', ffprobe:'VSP_FFPROBE', node:'VSP_NODE', blender:'VSP_BLENDER'}[name];
  if (key && env[key]) return env[key];
  const api = os === 'win32' ? win32 : posix;
  const exe = os === 'win32' ? name + '.exe' : name;
  const dirs = (env.PATH || '').split(os === 'win32' ? ';' : delimiter).filter(Boolean);
  if (os === 'darwin') dirs.push('/opt/homebrew/bin', '/usr/local/bin');
  if (os === 'win32') dirs.push(win32.join(env.LOCALAPPDATA || '', 'Microsoft/WinGet/Links'),
    win32.join(env.ProgramData || 'C:/ProgramData', 'chocolatey/bin'), 'C:/ffmpeg/bin');
  for (const dir of dirs) { const p = api.join(dir, exe); if (existsSync(p)) return p; }
  if (name === 'blender') return null;
  const cmd = os === 'darwin' ? 'brew install ffmpeg node' : os === 'win32' ?
    'winget install -e --id Gyan.FFmpeg; winget install -e --id OpenJS.NodeJS.LTS' : 'sudo apt-get install -y ffmpeg nodejs npm';
  throw Error(`${name} missing. Install with: ${cmd}`);
}
export function memAvailableMB() {
  try { const m = readFileSync('/proc/meminfo', 'utf8').match(/MemAvailable:\s+(\d+)/); return m ? Math.round(+m[1] / 1024) : Math.round(freemem()/1048576); } catch { return Math.round(freemem()/1048576); }
}
export function run(cmd, argv) {
  return new Promise((ok, fail) => { const p = spawn(['ffmpeg','ffprobe','node','blender'].includes(cmd) ? toolPath(cmd) : cmd, argv, {stdio: ['ignore', 'ignore', 'pipe']}); let err = '';
    p.stderr.on('data', x => err = (err + x).slice(-4000)); p.on('error', fail); p.on('close', c => c === 0 ? ok() : fail(Error(`${cmd} exit ${c}: ${err}`))); });
}
export function probe(file) {
  const p = spawnSync(toolPath('ffprobe'), ['-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,nb_read_frames,r_frame_rate', '-of', 'json', file], {encoding: 'utf8'});
  if (p.status !== 0) return null; try { return JSON.parse(p.stdout).streams?.[0] || null; } catch { return null; }
}
