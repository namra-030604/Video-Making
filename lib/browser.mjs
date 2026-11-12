// browser.mjs - zero-dependency headless Chrome driver for frame-exact video rendering.
// Talks to Chrome over --remote-debugging-pipe (no debugging port is opened).
// The project folder is served on a random 127.0.0.1 port (loopback only) so pages can
// fetch() their JSON/fonts; if a local server cannot listen, it falls back to file://.
//
// Page contract (either style works):
//   canvas: <canvas id="art"> (or the first <canvas> on the page)
//   ready : window.ready (Promise) or window.READY === true when fonts/assets are loaded
//   frame : window.renderFrame(t) or window.seek(t)  (may return a Promise; must be a pure function of t)
//   init  : optional window.init(data) called once with {project, words, meta} injected by the driver
//
// Chrome is found from $CHROME, then the pinned pack cache, then common system names
// (chrome-headless-shell installed by `install.sh --with-chrome`).
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {readFile, mkdir, rm, readdir, realpath} from 'node:fs/promises';
import {existsSync, createWriteStream} from 'node:fs';
import * as path from 'node:path';
import {join, extname, resolve, win32, posix} from 'node:path';
import {homedir, platform, arch} from 'node:os';
import {fileURLToPath, pathToFileURL} from 'node:url';
const PACK_ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));

const MIME = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.css':'text/css','.ttf':'font/ttf','.otf':'font/otf','.woff':'font/woff','.woff2':'font/woff2','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml','.wav':'audio/wav','.mp3':'audio/mpeg','.mp4':'video/mp4'};
const sleep = ms => new Promise(r => setTimeout(r, ms));

export function cacheDir() {
  return process.env.VSP_CACHE || join(process.env.XDG_CACHE_HOME || join(homedir(), '.cache'), 'video-skill-pack');
}

export function insideRoot(base, file, pathApi = path) {
  const rel = pathApi.relative(pathApi.resolve(base), pathApi.resolve(file));
  return rel === '' || (rel !== '..' && !rel.startsWith('..' + pathApi.sep) && !pathApi.isAbsolute(rel));
}

/** Resolve an HTTP request target under one of the three permitted roots. */
export function mapRequestPath(requestTarget, {root, fontsRoot, packRoot}, pathApi = path) {
  if (typeof requestTarget !== 'string' || !requestTarget.startsWith('/') || requestTarget.startsWith('//'))
    throw Error('invalid request path');
  // Parse as a URL for syntax, but inspect the raw path before WHATWG URL dot-segment normalization.
  const parsed = new URL(requestTarget, 'http://127.0.0.1');
  if (parsed.origin !== 'http://127.0.0.1') throw Error('invalid request origin');
  const rawPath = requestTarget.split(/[?#]/, 1)[0];
  const decoded = decodeURIComponent(rawPath);
  if (decoded.includes('\\') || decoded.includes('\0') || decoded.startsWith('//')) throw Error('invalid path separator');
  let segments = decoded.split('/').slice(1);
  if (segments.some(s => s === '.' || s === '..' || s.includes(':'))) throw Error('outside root');
  let base = root;
  if (segments[0] === '__vsp' && segments[1] === 'fonts') {
    base = fontsRoot; segments = segments.slice(2);
  } else if (segments[0] === '__vsp' && segments[1] === 'pack') {
    base = packRoot; segments = segments.slice(2);
  }
  if (!base) throw Error('missing server root');
  if (!segments.length || (segments.length === 1 && segments[0] === '')) segments = ['index.html'];
  const file = pathApi.resolve(base, ...segments);
  if (!insideRoot(base, file, pathApi)) throw Error('outside root');
  return {file, base};
}

export function requestPathToFile(requestTarget, roots, pathApi = path) {
  return mapRequestPath(requestTarget, roots, pathApi).file;
}

export function pageFileURL(root, page) {
  const file = path.resolve(root, page);
  if (!insideRoot(root, file)) throw Error('page outside root');
  return pathToFileURL(file).href;
}

export function pageHttpURL(root, page, origin, pathApi = path) {
  const file = pathApi.resolve(root, page);
  if (!insideRoot(root, file, pathApi)) throw Error('page outside root');
  const rel = pathApi.relative(pathApi.resolve(root), file);
  const url = new URL(origin);
  url.pathname = '/' + rel.split(pathApi.sep).map(encodeURIComponent).join('/');
  return url.href;
}
export function chromeCandidates(os = platform(), cpu = arch(), env = process.env, cache = cacheDir()) {
  const folder = os === 'win32' ? 'chrome-headless-shell-win64' : os === 'darwin' ?
    (cpu === 'arm64' ? 'chrome-headless-shell-mac-arm64' : 'chrome-headless-shell-mac-x64') : 'chrome-headless-shell-linux64';
  const binary = os === 'win32' ? 'chrome-headless-shell.exe' : 'chrome-headless-shell';
  const names = os === 'win32' ? ['chrome.exe', 'msedge.exe', 'chromium.exe', binary] :
    ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome', binary];
  const dirs = (env.PATH || '').split(os === 'win32' ? ';' : ':').filter(Boolean);
  const known = os === 'darwin' ? ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'] :
    os === 'win32' ? [env.PROGRAMFILES, env['PROGRAMFILES(X86)'], env.LOCALAPPDATA].filter(Boolean)
      .flatMap(d => [win32.join(d, 'Google/Chrome/Application/chrome.exe'), win32.join(d, 'Microsoft/Edge/Application/msedge.exe')]) : [];
  return {folder, binary, system: [...dirs.flatMap(d => names.map(n => (os === 'win32' ? win32 : posix).join(d, n))), ...known], cache};
}
export function orderedChromeCandidates({os = platform(), cpu = arch(), env = process.env,
  cache = cacheDir(), versions = [], exists = existsSync} = {}) {
  const {folder, binary, system} = chromeCandidates(os, cpu, env, cache);
  const pathApi = os === 'win32' ? win32 : posix;
  const pinned = [...versions].sort((a, b) => b.localeCompare(a, undefined, {numeric: true}))
    .map(version => pathApi.join(cache, 'chrome', version, folder, binary));
  return [...(env.CHROME ? [env.CHROME] : []), ...pinned, ...system].filter(exists);
}
export async function findChrome() {
  if (process.env.CHROME) { if (existsSync(process.env.CHROME)) return process.env.CHROME; throw Error('CHROME is set but does not exist: ' + process.env.CHROME); }
  const cache = cacheDir();
  const base = join(cache, 'chrome');
  const versions = existsSync(base) ? await readdir(base) : [];
  const candidates = orderedChromeCandidates({cache, versions});
  if (candidates.length) return candidates[0];
  throw Error('Chrome not found. Set CHROME or run: python vsp.py install --with-chrome');
}

function serve(root) {
  return new Promise((ok, fail) => {
    const s = createServer(async (req, res) => {
      if (process.env.VSP_DEBUG) console.error('serve', req.url);
      try {
        const {file, base} = mapRequestPath(req.url, {root, fontsRoot: join(cacheDir(), 'fonts'), packRoot: PACK_ROOT});
        if (!insideRoot(await realpath(base), await realpath(file))) throw Error('outside root');
        const data = await readFile(file);
        res.writeHead(200, {'Content-Type': MIME[extname(file).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store'});
        res.end(data);
      } catch (e) { if (process.env.VSP_DEBUG) console.error('serve 404', req.url, e.message); res.writeHead(404); res.end('missing'); }
    });
    s.once('error', fail);
    s.listen(0, '127.0.0.1', () => ok(s));
  });
}

class PipeCDP {
  constructor(chrome) {
    this.chrome = chrome; this.seq = 0; this.pending = new Map(); this.buf = Buffer.alloc(0);
    chrome.stdio[4].on('data', b => this.receive(b));
    chrome.stdio[4].on('error', e => this.fail(e));
    chrome.stdio[3].on('error', e => this.fail(e));
    chrome.on('exit', () => this.fail(Error('Chrome exited')));
  }
  receive(b) {
    this.buf = Buffer.concat([this.buf, b]);
    for (;;) {
      const at = this.buf.indexOf(0); if (at < 0) break;
      const raw = this.buf.subarray(0, at).toString(); this.buf = this.buf.subarray(at + 1);
      if (!raw) continue;
      const m = JSON.parse(raw);
      if (m.id && this.pending.has(m.id)) { const p = this.pending.get(m.id); this.pending.delete(m.id); m.error ? p.reject(Error(JSON.stringify(m.error))) : p.resolve(m.result); }
    }
  }
  fail(e) { for (const p of this.pending.values()) p.reject(e); this.pending.clear(); }
  send(method, params = {}, sessionId = this.sessionId) {
    const id = ++this.seq, msg = {id, method, params}; if (sessionId) msg.sessionId = sessionId;
    this.chrome.stdio[3].write(JSON.stringify(msg) + '\0');
    return new Promise((resolve, reject) => this.pending.set(id, {resolve, reject}));
  }
  async eval(expression) {
    const r = await this.send('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
    if (r.exceptionDetails) throw Error('page error: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
    return r.result.value;
  }
  close() { try { this.chrome.stdio[3].end(); } catch {} }
}

const FRAME_FN = `(window.renderFrame||window.seek)`;
const CANVAS = `(document.getElementById('art')||document.querySelector('canvas'))`;

/** Launch headless Chrome, open <root>/<page>, wait for ready, optionally call window.init(initData). */
export async function launch({root = process.cwd(), page = 'index.html', tag = 'work', initData = null, width, height} = {}) {
  root = resolve(root);
  const chromePath = await findChrome();
  const work = join(cacheDir(), 'chrome-profiles', tag + '-' + process.pid);
  await rm(work, {recursive: true, force: true}); await mkdir(work, {recursive: true});
  const log = createWriteStream(join(work, 'chrome.log'));
  let server = null, url;
  try { if (process.env.VSP_NO_SERVER) throw Error('server disabled'); server = await serve(root); url = pageHttpURL(root, page, `http://127.0.0.1:${server.address().port}/`); }
  catch { url = pageFileURL(root, page); }
  const args = ['--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--disable-background-networking',
    '--disable-sync', '--no-first-run', '--no-default-browser-check', '--mute-audio', '--hide-scrollbars',
    '--allow-file-access-from-files', '--disable-crashpad-for-testing', '--remote-debugging-pipe', `--user-data-dir=${work}`,
    ...(width && height ? [`--window-size=${width},${height}`] : []), 'about:blank'];
  if (/chrome-headless-shell(\.exe)?$/i.test(chromePath)) args.shift(); // headless shell is always headless
  const chrome = spawn(chromePath, args, {stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe'],
    env: {...process.env, XDG_DATA_HOME: join(work, 'xdg-data'), XDG_CACHE_HOME: join(work, 'xdg-cache')}});
  chrome.stderr.pipe(log);
  const cdp = new PipeCDP(chrome);
  const close = async () => {
    cdp.close(); chrome.kill('SIGTERM');
    await new Promise(ok => { if (chrome.exitCode !== null) return ok(); chrome.once('exit', ok); setTimeout(ok, 4000); });
    server?.close(); log.end(); await rm(work, {recursive: true, force: true}).catch(() => {});
  };
  try {
    let target;
    for (let i = 0; i < 100 && !target; i++) { const ts = await cdp.send('Target.getTargets', {}, null); target = ts.targetInfos.find(x => x.type === 'page'); if (!target) await sleep(100); }
    if (!target) throw Error('no Chrome page target');
    cdp.sessionId = (await cdp.send('Target.attachToTarget', {targetId: target.targetId, flatten: true}, null)).sessionId;
    await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
    // the very first navigation can be aborted while Chrome finishes loading about:blank, so retry a few times
    for (let i = 0; i < 5; i++) {
      const nav = await cdp.send('Page.navigate', {url});
      if (process.env.VSP_DEBUG) console.error('navigate', url, JSON.stringify(nav));
      if (!nav.errorText) break;
      if (i === 4) throw Error(`cannot open ${url}: ${nav.errorText}`);
      await sleep(300 * (i + 1));
    }
    let ready = false, lastErr = null;
    for (let i = 0; i < 300 && !ready; i++) {
      try {
        ready = await cdp.eval(`(async()=>{ if(document.readyState!=='complete') return false; if(window.ready) await window.ready; else if(window.READY!==true && window.fontLoaded!==true) return false; return typeof ${FRAME_FN}==='function' && !!${CANVAS}; })()`);
      } catch (e) { lastErr = e; }
      if (!ready) await sleep(100);
      if (!ready && process.env.VSP_DEBUG && i % 20 === 0) console.error('ready-debug', await cdp.eval('JSON.stringify({u:location.href,rs:document.readyState,r:typeof window.ready,f:typeof window.renderFrame,c:!!document.querySelector("canvas")})').catch(e => e.message));
    }
    if (!ready) throw Error('page never became ready (need window.ready/READY and renderFrame/seek + canvas)' + (lastErr ? ': ' + lastErr.message : ''));
    if (initData) await cdp.eval(`(async()=>{ if(window.init) await window.init(${JSON.stringify(initData)}); return true; })()`);
    return {cdp, chrome, url, close,
      /** draw frame at t, return metadata object from renderFrame */
      meta: (t, extra = '') => cdp.eval(`(async()=>{ const m = await ${FRAME_FN}(${Number(t).toFixed(6)}${extra}); return m||{}; })()`),
      /** draw frame at t, return PNG Buffer */
      png: async (t, extra = '') => Buffer.from(await cdp.eval(`(async()=>{ await ${FRAME_FN}(${Number(t).toFixed(6)}${extra}); return ${CANVAS}.toDataURL('image/png').split(',')[1]; })()`), 'base64'),
      info: () => cdp.eval(`({W:${CANVAS}.width,H:${CANVAS}.height,DURATION:window.DURATION??null,FPS:window.FPS??null})`)};
  } catch (e) { await close(); throw e; }
}
