---
component: qc-and-render
description: >-
  The pack's restart-safe render pipeline and automatic quality gates: review stills and blank scan, determinism
  check, rendering in verified parts with content hashes, ffmpeg mux, small copy, subtitle QC, framediff, and
  qc_final.py (resolution, fps, duration, A/V sync, black/static/near-blank, loudness, true peak, size, pace,
  alignment). Use to render any project, resume a crashed render, or prove a video is done.
---
# QC and render

`PACK` = this repo; `PY=$(cat $PACK/.vsp-state/python)` (the venv python chosen by install.sh).

## One command
`bash $PACK/scripts/build.sh <project>`: voice -> align -> audio -> stills -> render -> subtitle QC -> final QC.
Every step skips itself when its inputs are unchanged, so re-running after a crash continues where it stopped.
`bash $PACK/scripts/new_project.sh <folder>` scaffolds a project from `examples/hello-world`.

## project.json (minimum)
```json
{ "name": "demo", "width": 1080, "height": 1920, "fps": 30, "page": "index.html",
  "lines": ["..."], "voice": {"voice": "af_heart", "speed": 1.0},
  "subtitles": {"safe_top": 0.72, "safe_bottom": 0.90, "safe_side": 0.06, "font_px": 68},
  "audio": {"lufs": -14, "true_peak": -1.5, "bed": "pad"},
  "render": {"part_frames": 150, "crf": 18, "threads": 2, "small_height": 720, "hash_dirs": ["scene", "assets"]},
  "qc": {"max_mb": 50, "freeze_s": 0.75, "wpm_range": [150, 172]}, "output": "out/demo.mp4" }
```
`render.hash_dirs` (default `["scene"]`) lists folders whose files are hashed with the page and project.json;
change anything there and the affected parts re-render. `qc.max_mb` defaults to 200.
Duration comes from `audio/voice_meta.json` for narrated projects, or `"duration"` for silent motion pieces.

## Steps and what they prove
| Step | Command | Output / gate |
|---|---|---|
| Stills | `node scripts/stills.mjs --project P --n 8 --scan` | `out/stills/still_NN.png`, `contact.png`; scan flags near-blank and identical samples |
| Determinism | `node scripts/stills.mjs --project P --check` | forward vs reverse render, no pixel > 8 levels apart, no running CSS animations |
| Render | `node scripts/render.mjs --project P` | `out/parts/part_NNN.mp4` + `.json` (source hash); a part is skipped when its hash matches; concat + AAC 192k mux; small copy when `small_height` is set |
| Subtitles | `node scripts/subtitle_qc.mjs --project P` | safe area every 0.1 s; word onset within 1 frame |
| Motion | `$PY scripts/framediff.py out/<name>.mp4` | no static stretch > 0.75 s, no full-screen flash |
| Final | `$PY scripts/qc_final.py --project P` | PASS/FAIL table, `out/qc/qc_final.json`, `out/qc/contact_sheet.png`; exit 1 on FAIL |

`qc_final.py` gates: resolution, fps, yuv420p, duration +/-0.15 s, A/V end difference <= 0.1 s, -14 +/-0.5 LUFS,
TP <= -1.5 dBTP, no black >= 0.5 s, no freeze >= 0.75 s, no near-blank sample (luma < 12) at 4 fps, size <=
`qc.max_mb`, pace 150-172 wpm (informational under 15 s), >= 97% words aligned, subtitle QC.

## Render contract (your page)
- `window.ready` Promise or `window.READY = true`; `window.renderFrame(t)` or `window.seek(t)`; canvas `#art`
  (or the first canvas); optional `window.init({project, words, meta})`, called once after ready.
- The page is served from the project folder on a random 127.0.0.1 port (file:// fallback); `/__vsp/fonts/<file>`
  maps to the installed OFL fonts and `/__vsp/pack/<path>` to this repo (e.g. `/__vsp/pack/video-making/components/motion-graphics/fx.js`).
- Pure function of t: no timers, no Math.random, no Date.now, no state carried between frames.

## Memory and restarts
- `free -h` before starting; render.mjs waits for >= 800 MB available before each part; one render at a time.
- `VSP_DEBUG=1` prints browser and server details; `CHROME=/path/to/chrome` forces a browser;
  `VSP_NO_SERVER=1` uses file:// instead of the local server; `VSP_CACHE` moves the download cache.
- After a crash just re-run the same command. Delete `out/parts/` only to force a full re-render.
