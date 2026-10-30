import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
const root = new URL('..', import.meta.url).pathname;
const read = p => readFileSync(join(root, p), 'utf8');
let failures = 0;
function check(label, ok, detail = '') {
  console.log(`${ok ? 'PASS' : 'FAIL'} ${label}${detail ? ' — ' + detail : ''}`);
  if (!ok) failures++;
}
const fxSource = read('fx.js');
const stub = {};
try {
  new Function('window', fxSource)(stub);
  check('fx.js parses and attaches window.FX', !!stub.FX);
} catch (err) { check('fx.js parses and attaches window.FX', false, err.message); }
for (const forbidden of ['Math.random', 'Date.now', 'performance.now']) {
  check(`fx.js excludes ${forbidden}`, !fxSource.includes(forbidden));
}
const skill = read('COMPONENT.md');
const front = skill.match(/^---\n([\s\S]*?)\n---\n/);
check('COMPONENT.md frontmatter has component and description', !!front && /^component:\s*motion-graphics\s*$/m.test(front[1]) && /^description:\s*\S+/m.test(front[1]));
const guides = [
  'easing','kinetic-text','text-mask-reveal','particle-text','charts','counters',
  'glass-cards','match-cuts','transitions','glitch','halftone','camera-and-parallax',
  'screen-shake','stroke-draw-handwriting','ink-watercolor','shape-morph',
  'light-and-glow','map-and-timeline'
];
for (const name of guides) {
  const file = `guides/${name}.md`;
  if (!existsSync(join(root, file))) { check(file, false, 'missing'); continue; }
  const body = read(file);
  const refs = [...body.matchAll(/FX\.([A-Za-z][A-Za-z0-9]*)/g)].map(m => m[1]);
  const valid = refs.some(ref => stub.FX && Object.hasOwn(stub.FX, ref));
  check(file, valid, valid ? '' : 'no existing FX reference');
}
if (failures) process.exitCode = 1;
