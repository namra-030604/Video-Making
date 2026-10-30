---
name: video-skill-pack
description: >-
  Entry point for the Video-Making skill pack: which skill to load for which video task, the 7-step pipeline
  (voice, align, audio, stills, render, subtitle QC, final QC), and the commands to scaffold, build and check a
  project. Load this first for any request to make, edit, caption, narrate or render a video with code.
---
# Video skill pack (router)

`PACK` = the folder where this repo was cloned (contains `install.sh`). Run `bash $PACK/install.sh verify` once per
session; if anything FAILs, fix it before making a video (see `AGENT_INSTALL.md` troubleshooting).

## Which skill
| Task | Load |
|---|---|
| Any new narrated video (explainer, story, short) - the full standard and gates | `video-production-standard` |
| Write or fit the narration | `script-writing` |
| Voice, music, SFX, loudness | `voice-and-audio` |
| Word-by-word captions | `subtitles-karaoke` |
| Music-led motion piece, title sequence, promo | `motion-studio` |
| A specific effect (kinetic text, charts, glitch, particles, maps...) | `motion-graphics` (18 guides + `fx.js`) |
| Vertical 9:16 layout or reframing landscape footage | `vertical-9-16-framing` |
| Cutting footage into Shorts, launch videos, explainer modes | `short-form-editing` |
| Render, resume, prove it is done | `qc-and-render` |
| Before starting and whenever something breaks | `lessons-from-failures` |

## Pipeline
```bash
bash $PACK/scripts/new_project.sh my-video          # scaffold from examples/hello-world
# edit my-video/project.json (lines, size, voice) and my-video/index.html (the scene)
bash $PACK/scripts/build.sh my-video                # voice -> align -> audio -> stills -> render -> QC
```
Output: `my-video/out/<name>.mp4`, review images in `out/stills/`, QC in `out/qc/`. Every step is restart-safe.

## Non-negotiables
1. Scenes are pure functions of time (`renderFrame(t)`), drawn on one canvas, rendered frame by frame.
2. Free local voices only (Kokoro default); never clone a real voice; speed 1.0, no time-stretch.
3. Captions from forced alignment, inside the safe zone.
4. Look at stills before the full render; run `stills.mjs --check` for determinism.
5. A video is done only when `qc_final.py` prints OVERALL PASS. Report honestly what was not checked.
6. Record every third-party asset and its license in the project's `assets/CREDITS.md`.
