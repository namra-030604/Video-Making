import test from 'node:test';
import assert from 'node:assert/strict';
import path, {win32, posix} from 'node:path';
import {spawnSync} from 'node:child_process';
import {insideRoot, requestPathToFile, pageFileURL, pageHttpURL, chromeCandidates, orderedChromeCandidates} from '../lib/browser.mjs';

const winRoots = {root: 'C:\\project', fontsRoot: 'C:\\cache\\fonts', packRoot: 'C:\\pack'};
const posixRoots = {root: '/project', fontsRoot: '/cache/fonts', packRoot: '/pack'};

test('Windows request mapping: drive paths, mounts and spaces', () => {
  assert.equal(requestPathToFile('/', winRoots, win32), 'C:\\project\\index.html');
  assert.equal(requestPathToFile('/scene/index.html', winRoots, win32), 'C:\\project\\scene\\index.html');
  assert.equal(requestPathToFile('/a%20b.html?x=1', winRoots, win32), 'C:\\project\\a b.html');
  assert.equal(requestPathToFile('/__vsp/fonts/Inter.ttf', winRoots, win32), 'C:\\cache\\fonts\\Inter.ttf');
  assert.equal(requestPathToFile('/__vsp/pack/lib/browser.mjs', winRoots, win32), 'C:\\pack\\lib\\browser.mjs');
  assert.equal(insideRoot('C:\\project', 'C:\\project\\index.html', win32), true);
  assert.equal(insideRoot('C:\\project', 'D:\\project\\index.html', win32), false);
  assert.equal(insideRoot('C:\\project', 'C:\\project2\\index.html', win32), false);
});

test('Windows request mapping rejects traversal, encoded separators and drives', () => {
  for (const request of ['/../secret', '/scene/../../secret', '/%2e%2e/secret',
                         '/scene/%2e%2e/secret', '/scene%5c..%5csecret',
                         '/scene\\..\\secret', '/D:/secret', '/D%3a/secret', '//server/share/secret']) {
    assert.throws(() => requestPathToFile(request, winRoots, win32), Error, request);
  }
});

test('Windows UNC roots stay within the same share', () => {
  const roots = {...winRoots, root: '\\\\server\\share\\project'};
  assert.equal(requestPathToFile('/scene.html', roots, win32), '\\\\server\\share\\project\\scene.html');
  assert.equal(insideRoot(roots.root, '\\\\server\\share\\project\\scene.html', win32), true);
  assert.equal(insideRoot(roots.root, '\\\\server\\other\\project\\scene.html', win32), false);
});

test('POSIX request mapping and containment', () => {
  assert.equal(requestPathToFile('/', posixRoots, posix), '/project/index.html');
  assert.equal(requestPathToFile('/scene.html', posixRoots, posix), '/project/scene.html');
  assert.equal(requestPathToFile('/__vsp/pack/lib/browser.mjs', posixRoots, posix), '/pack/lib/browser.mjs');
  assert.equal(insideRoot('/project', '/project/index.html', posix), true);
  assert.equal(insideRoot('/project', '/project2/index.html', posix), false);
  for (const request of ['/../x', '/%2e%2e/x', '/x%5c..%5cx', '//host/share']) {
    assert.throws(() => requestPathToFile(request, posixRoots, posix), Error, request);
  }
});

test('file URL uses pathToFileURL and encodes spaces', () => {
  const url = pageFileURL(path.join(process.cwd(), 'a b'), 'index.html');
  assert.match(url, /^file:/);
  assert.match(url, /a%20b/);
  assert.match(url, /index.html$/);
  assert.throws(() => pageFileURL(process.cwd(), '../outside.html'), /outside root/);
});

test('HTTP page URLs use native path rules and encode names', () => {
  assert.equal(pageHttpURL('C:\\project', 'scene\\a b.html', 'http://127.0.0.1:321/', win32),
    'http://127.0.0.1:321/scene/a%20b.html');
  assert.equal(pageHttpURL('/project', 'scene/a b.html', 'http://127.0.0.1:321/', posix),
    'http://127.0.0.1:321/scene/a%20b.html');
  assert.throws(() => pageHttpURL('C:\\project', 'D:\\other\\x.html', 'http://127.0.0.1:321/', win32), /outside root/);
});

test('Chrome candidates include platform folders and names', () => {
  assert.equal(chromeCandidates('linux', 'x64', {PATH:'/bin'}, '/cache').folder, 'chrome-headless-shell-linux64');
  assert.equal(chromeCandidates('darwin', 'arm64', {PATH:'/bin'}, '/cache').folder, 'chrome-headless-shell-mac-arm64');
  assert.equal(chromeCandidates('darwin', 'x64', {PATH:'/bin'}, '/cache').folder, 'chrome-headless-shell-mac-x64');
  const win = chromeCandidates('win32', 'x64', {PATH:'C:\\bin;D:\\bin', PROGRAMFILES:'C:\\Program Files'}, 'C:\\cache');
  assert.equal(win.folder, 'chrome-headless-shell-win64');
  assert.ok(win.system.some(p => p.endsWith('chrome.exe')));
});

test('Chrome search order is override, newest pinned cache, then system', () => {
  const env = {CHROME: '/custom/chrome', PATH: '/usr/bin'};
  const present = new Set(['/custom/chrome',
    '/cache/chrome/130.0.10/chrome-headless-shell-linux64/chrome-headless-shell',
    '/cache/chrome/130.0.9/chrome-headless-shell-linux64/chrome-headless-shell',
    '/usr/bin/google-chrome']);
  const options = {os: 'linux', cpu: 'x64', env, cache: '/cache',
    versions: ['130.0.9', '130.0.10'], exists: candidate => present.has(candidate)};
  assert.deepEqual(orderedChromeCandidates(options), [...present]);
  delete env.CHROME;
  assert.equal(orderedChromeCandidates(options)[0], '/cache/chrome/130.0.10/chrome-headless-shell-linux64/chrome-headless-shell');
  present.delete('/cache/chrome/130.0.10/chrome-headless-shell-linux64/chrome-headless-shell');
  present.delete('/cache/chrome/130.0.9/chrome-headless-shell-linux64/chrome-headless-shell');
  assert.equal(orderedChromeCandidates(options)[0], '/usr/bin/google-chrome');
});

test('voice-only mode blocks direct video scripts with one message', () => {
  for (const script of ['stills.mjs', 'render.mjs', 'subtitle_qc.mjs']) {
    const result = spawnSync(process.execPath, [path.join(process.cwd(), 'scripts', script), '--project', '.'],
      {encoding: 'utf8', env: {...process.env, VSP_VOICE_ONLY: '1'}});
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /^Voice-only mode:/);
    assert.equal(result.stderr.trim().split('\n').length, 1);
  }
});
