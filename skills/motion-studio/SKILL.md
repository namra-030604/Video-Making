---
name: motion-studio
description: >-
  Build motion-graphics videos entirely from code: a seekable canvas page (window.seek(t) or renderFrame(t)),
  captured one frame at a time by headless Chrome and encoded with ffmpeg. Covers the render contract, a beat sheet on
  a BPM grid, the MS helper library (easing, springs, squash and stretch, cursor-driven UI, kinetic type, grain,
  bloom, flares, chromatic aberration, split screens, torn-paper collage, kaleidoscope), code-synthesized music and
  frame-exact SFX, the -14 LUFS mix, free CC0/CC-BY asset fetching with credits, framediff and a self-critique
  contact-sheet loop. Use for promos, launch videos, UI demos and any motion-design piece.
---
# motion-studio

You are a motion designer who builds video from code. Every frame is drawn by code; fetch only what code
cannot draw. `PACK` below means the folder this repo was cloned into.

## 0. Start
```bash
bash $PACK/skills/motion-studio/scripts/new_project.sh my-promo            # 1920x1080 @ 60 fps
bash $PACK/skills/motion-studio/scripts/new_project.sh my-short --vertical # 1080x1920
```
This copies `templates/index.html`, `templates/mslib.js`, `templates/beats.json` and writes `project.json`
(size, fps, duration, render settings). Read `references/look-and-motion.md` and `references/critique.md` once.
For effect recipes (kinetic text, charts, glitch, maps, ...), use the `motion-graphics` skill and its `fx.js`.

## 1. Render contract (the pack renderer enforces it)
- One `index.html` page drawing on a `<canvas>` (id `art` or the first canvas on the page).
- `window.seek(t)` or `window.renderFrame(t)` redraws the WHOLE frame from `t` alone (it may be async).
- Set `window.READY = true` (or resolve `window.ready`) only after fonts, images and JSON have loaded.
  `await MS.loadPackFonts()` loads the OFL fonts that install.sh put in the cache (Inter, Caveat).
- Forbidden: CSS transitions/animations, `setTimeout`/`setInterval`/`requestAnimationFrame` for motion,
  `Math.random`, `Date.now`/`performance.now`, any state carried between frames. Seeded randomness only:
  `MS.rng(seed)`, `MS.hash(i, seed)`, `MS.noise1`.
- Check determinism: `node $PACK/scripts/stills.mjs --project . --check` (same t, same pixels, any order).
- Render: `node $PACK/scripts/render.mjs --project .` (parts of `render.part_frames` frames, each verified and
  skipped on re-run if unchanged; muxes `audio/mix.wav` when present).

## 2. Beat sheet first (beats.json), before any drawing code
Fields: `title, bpm, fps, size, duration, seed, beats[{id, t, section, action, cut, sfx[{t, type, gain}]}]`.
- 120 BPM = 0.5 s per beat. `"cut": true` beats sit on the grid; the music bed lands an impact there.
- Every visual action that should make a sound gets an `sfx` cue at the same time as the visual.
- `python3 scripts/beatsheet.py --new 10 --bpm 120 > beats.json`, fill it in, then
  `python3 scripts/beatsheet.py beats.json` (grid, hook at 0.0 s, dead-air gaps, sfx types; `--snap`).

## 3. Motion
- Ease everything (`MS.ease.inOutCubic/inOutSine/inOutExpo`, `outBack`, `outElastic`, `outBounce`, `MS.spring`).
  Squash and stretch on hits (`MS.squash(MS.hitWobble(t, tHit))`). Stagger related elements 0.05-0.12 s.
- Hook: something big moves at 0.0 s; the promise is on screen by about 1.5 s.
- UI demos: a cursor drives every change (`MS.cursorAt` + `MS.drawCursor`).
- Nothing static: drifting backgrounds, `MS.pulse(t, bpm)` breathing, parallax layers.

## 4. Look
- Avoid: a centred title on a plain gradient; everything fading in; full-screen flashing; anything covering the
  title or hero object.
- Toolkit in `mslib.js`: `MS.grain`, `MS.bloom`, `MS.flare`, `MS.chromatic`, `MS.archival`, `MS.kineticLine`,
  `MS.splitScreen`, `MS.paperScrap`/`MS.tearReveal`/`MS.tornPath`, `MS.kaleidoscope`, `MS.neon`, `MS.vignette`,
  palettes `MS.palettes.darkSkyNeon | warmNeutral | paper | archival`.
- Transitions: mask the outgoing scene (clip, tear, split) so text from two scenes never overlaps.

## 5. Sound (all synthesized, no downloads)
```bash
python3 scripts/synth_audio.py bed  --beats beats.json --out audio/music.wav   # --style bed|drive|chill
python3 scripts/synth_audio.py cues --beats beats.json --out audio/sfx.wav     # click, whoosh, pop, impact, riser, tick
python3 scripts/mix.py --music audio/music.wav --sfx audio/sfx.wav [--voice audio/voice.wav] \
        --video out/<name>.mp4 --out out/final.mp4                              # ducked, -14 LUFS, TP -1.5
python3 scripts/mix.py --measure out/final.mp4
```
(Use the venv python named in `$PACK/.vsp-state/python`.) For narrated pieces, use the pack pipeline instead:
`make_voice.py` -> `align_words.py` -> `make_audio.py` (see the `voice-and-audio` skill).

## 6. Images and video (only what code cannot draw)
`python3 scripts/fetch_assets.py "film camera" --n 2 --outdir assets` searches Openverse and Wikimedia Commons,
keeps only CC0 / public domain / CC BY / CC BY-SA, and writes `assets/credits.json` + `assets/CREDITS.md`. Put the
credits in the video description. `--cutout` needs rembg, which this pack does not install. No people in fetched
images unless the user asked. This needs network access.

## 7. Self-critique loop (before showing anything)
1. `python3 scripts/contact_sheet.py --project . --every-beat --mid` -> `out/contact_sheet.png`. Open it and look.
2. Score 1-10: readability, motion quality, brand accuracy, sound sync, composition, typography, hook strength.
3. Fix the worst 3 problems, re-render the sheet, re-score, until every axis is 8+ (`references/critique.md`).
4. `python3 $PACK/scripts/framediff.py out/final.mp4` -> no static stretch > 0.75 s, no full-screen flash.

## 8. Deliverables
`out/<name>.mp4`, the editable project (index.html, mslib.js, beats.json, project.json, assets/),
`out/contact_sheet.png`, the last scorecard, framediff JSON, `assets/CREDITS.md` if assets were used, CHANGELOG.md.
On iteration, copy the previous mp4 to `out/v<N>/` first and add a changelog entry.

## 9. Characters and lip-sync (when the piece has characters)
- Model sheet per character before any scene (front, 3/4, side, back, expressions, mouth chart, palette, spec text);
  rigged parts with pivots; original designs only.
- Mouths come from phoneme timing of the real audio (see `video-production-standard` section 6), never loudness.

Speed reference (measured on an 8-core box): the 3 s 1920x1080 @ 60 fps starter renders in about 55 s.
