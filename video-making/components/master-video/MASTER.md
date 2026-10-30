---
component: master-video
description: >-
  The master video component: end-to-end orchestration of a complete video, from brief to a QC-passed mp4.
  It runs the phases in order and says which sub-component to open in each phase. The router (../../SKILL.md)
  sends every "make a whole video" request here.
---
# Master video: full end-to-end orchestration

`PACK` is the repo root (how to find it: see "Find the pack root" in `../../SKILL.md`). All commands below use
`$PACK/...`; component links are relative to this file. Run `bash $PACK/install.sh verify` once per session and
fix every FAIL before starting.

## Phase map (do them in this order; open each component when you reach its phase)
| # | Phase | Open | Produces | Gate before moving on |
|---|---|---|---|---|
| 0 | Pre-flight: read the failure history and the standard | [lessons-from-failures](../lessons-from-failures/COMPONENT.md), [video-production-standard](../video-production-standard/COMPONENT.md) | upgraded brief, `PROGRESS.md` | brief states length, aspect, audience, style, sources |
| 1 | Script / text generation | [script-writing](../script-writing/COMPONENT.md) | `project.json -> lines`, beat list | word count fits the target at ~165 wpm; hook in the first 2 s |
| 2 | Format and layout | [vertical-9-16-framing](../vertical-9-16-framing/COMPONENT.md) (9:16) or the standard (16:9) | width/height/fps, safe zones | captions/title zones decided |
| 3 | Voice, alignment, music, SFX, loudness | [voice-and-audio](../voice-and-audio/COMPONENT.md) | `audio/voice.wav`, `align/words.json`, `audio/mix.wav` | pace 150-172 wpm (>15 s), >= 97% words aligned, -14 LUFS |
| 4 | Visuals: scenes and effects | [motion-graphics](../motion-graphics/COMPONENT.md) (18 guides), [motion-studio](../motion-studio/COMPONENT.md) for music-led pieces | `index.html` with `renderFrame(t)` | every beat has motion; nothing static > 0.75 s |
| 5 | Captions | [subtitles-karaoke](../subtitles-karaoke/COMPONENT.md) | subtitle drawing + `subtitleBoxes` | subtitle QC PASS |
| 6 | Short-form edit choices (if a Short/Reel/launch video) | [short-form-editing](../short-form-editing/COMPONENT.md) | hook bar, keyword colours, payoff cut | hook visible < 2 s |
| 7 | Review stills, determinism, restart-safe render | [qc-and-render](../qc-and-render/COMPONENT.md) | `out/stills/contact.png`, `out/<name>.mp4` | stills look right; `stills.mjs --check` PASS |
| 8 | Final QC and hand-off | [qc-and-render](../qc-and-render/COMPONENT.md) | `out/qc/qc_final.json`, contact sheet | `qc_final.py` OVERALL PASS |

## Commands
```bash
bash $PACK/scripts/new_project.sh my-video                 # phase 0-2: scaffold (copies examples/hello-world)
# phase 1-6: edit my-video/project.json (lines, size, voice, subtitles, audio) and my-video/index.html (scenes)
node $PACK/scripts/stills.mjs --project my-video --n 8 --scan   # look at out/stills/contact.png before rendering
node $PACK/scripts/stills.mjs --project my-video --check        # determinism (pure function of t)
bash $PACK/scripts/build.sh my-video                       # voice -> align -> audio -> stills -> render -> subtitle QC -> final QC
"$(cat $PACK/.vsp-state/python)" $PACK/scripts/framediff.py my-video/out/my-video.mp4   # optional motion/flash check
```
`build.sh` is restart-safe: each step skips itself when its inputs are unchanged, so after a crash re-run it.
The Python steps use the interpreter recorded in `$PACK/.vsp-state/python` (the `.venv`).
Music-led pieces with no narration: `bash $PACK/video-making/components/motion-studio/scripts/new_project.sh <dir>`
and follow [motion-studio](../motion-studio/COMPONENT.md).

## Working rules (all phases)
1. Scenes are pure functions of time (`renderFrame(t)`), drawn on one canvas, rendered frame by frame.
2. Free local voices only (Kokoro default, Piper/espeak as alternatives); never clone a real voice; speed 1.0,
   no time-stretch; fit duration by editing words.
3. Captions come from forced alignment and stay inside the safe zone. MMS_FA is CC-BY-NC 4.0 (non-commercial):
   tell the user before using it for commercial work.
4. Look at stills before every full render. One heavy process at a time; `free -h` first.
5. Write progress to `PROGRESS.md` after each phase so a new session can resume.
6. A video is done only when `qc_final.py` prints OVERALL PASS. Report honestly what was not checked.
7. Record every third-party asset and its license in the project's `assets/CREDITS.md`.

## Hand-off message (what to tell the user)
Path of the mp4 (and small copy), duration, resolution, loudness, the QC table result, what you could not check,
and the credits for any third-party assets.
