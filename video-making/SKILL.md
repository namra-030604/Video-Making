---
name: video-making
description: >-
  The only entry point for all video work: making a full narrated or animated video, writing a video script,
  voice-over / narration / music / sound effects / loudness, motion graphics and effects (kinetic text, glitch,
  transitions, charts, maps), word-by-word karaoke captions, 9:16 vertical framing, cutting Shorts/Reels,
  rendering, resuming a failed render, and video QC. Read this router first; it sends you to the right component.
---
# Video-making router

This file only routes. Read the user's request, pick the row below, open that component and follow it.
Everything is free and local (Kokoro voice, headless Chrome, ffmpeg); no API keys.

## Find the pack root (`PACK`) first
```bash
SKILL_DIR="<folder containing this SKILL.md>"
PACK="${VSP_PACK:-$(cat "$SKILL_DIR/PACK_ROOT" 2>/dev/null || (cd "$(realpath "$SKILL_DIR")/.." && pwd))}"
test -f "$PACK/install.sh" && bash "$PACK/install.sh" verify    # once per session; fix any FAIL first
```
`install.sh` writes `PACK_ROOT` (the absolute repo path) into this folder, so it works for symlinked and copied
installs; `VSP_PACK` overrides it. Component paths below are relative to this file; commands use `$PACK`.

## How to route
1. Lower-case the request and find the row whose **keywords** match it best (most keywords matched; on a tie,
   the earlier row wins).
2. If the request asks for a **whole video** (or several areas at once), or nothing matches: use the default,
   the master video component.
3. While working, open further components the routed one links to (they are all inside `components/`).

## Routing table
| Intent | Keywords | Open | Run / first step |
|---|---|---|---|
| Something broke / avoid known mistakes | why, broke, broken, went wrong, black frame, blank, lessons, mistakes, avoid, debug | `components/lessons-from-failures/COMPONENT.md` | read the matching lesson, then the component it names |
| Production standard / quality bar | standard, checklist, quality bar, gates, blueprint, lip-sync, lip sync, character | `components/video-production-standard/COMPONENT.md` | apply the stage gates |
| Script / text generation | script, write, rewrite, hook, outline, wording, word count, wpm, storyboard, beats list, title text | `components/script-writing/COMPONENT.md` | words = seconds x 165 / 60; edit `project.json -> lines` |
| Voice, music, sound, loudness | voiceover, voice-over, voice over, voice, narration, narrate, tts, speech, music, background music, soundtrack, sfx, sound effect, sound, audio, loudness, lufs, mix, piper, kokoro | `components/voice-and-audio/COMPONENT.md` | `"$(cat $PACK/.vsp-state/python)" $PACK/scripts/make_voice.py --project <dir>` (then `align_words.py`, `make_audio.py`) |
| Captions / karaoke subtitles | captions, caption, subtitles, subtitle, karaoke, srt, vtt, closed captions, word highlight | `components/subtitles-karaoke/COMPONENT.md` | `node $PACK/scripts/subtitle_qc.mjs --project <dir>` |
| Maps / timelines | map, maps, route, geography, country, countries, timeline, history timeline | `components/motion-graphics/guides/map-and-timeline.md` | `bash $PACK/install.sh --with-maps` for real geography |
| Motion graphics / effects | glitch, transition, transitions, kinetic text, kinetic, particles, particle, chart, charts, graph, counter, glass, halftone, parallax, camera move, shake, morph, glow, ink, watercolor, handwriting, stroke, effect, effects, motion graphics, animate text | `components/motion-graphics/COMPONENT.md` | `<script src="/__vsp/pack/video-making/components/motion-graphics/fx.js">` then the matching guide |
| Music-led motion piece / promo | promo, trailer, title sequence, intro, logo reveal, beat sheet, beats, music-led, product video, launch trailer | `components/motion-studio/COMPONENT.md` | `bash $PACK/video-making/components/motion-studio/scripts/new_project.sh <dir>` |
| 9:16 vertical framing | vertical, 9:16, 9x16, portrait, reframe, crop, 1080x1920, letterbox | `components/vertical-9-16-framing/COMPONENT.md` | set width 1080 / height 1920; follow the zone layout |
| Short-form editing | shorts, short-form, reels, reel, tiktok, clip, clips, podcast, cut down, cold open, hook bar, payoff, launch video, viral | `components/short-form-editing/COMPONENT.md` | find the moment, cold open, hook bar, captions |
| Rendering / QC / restart-safe | render, rendering, re-render, resume, restart, crashed, failed, export, encode, qc, quality check, check the video, mp4, frames, determinism | `components/qc-and-render/COMPONENT.md` | `bash $PACK/scripts/build.sh <dir>` (re-run resumes) |
| **Full video (default)** | explainer, full video, whole video, make a video, create a video, make me a video, video about, animated video, story video, documentary, end to end, from scratch, short film, cartoon | `components/master-video/MASTER.md` | follow the phase map from phase 0 |

## Component index (all content lives here)
- `components/master-video/MASTER.md`: full end-to-end orchestration (phases 0-8).
- `components/video-production-standard/COMPONENT.md`: the production standard and stage gates.
- `components/lessons-from-failures/COMPONENT.md`: 20 lessons, pre-flight checklist, gates.
- `components/script-writing/COMPONENT.md`, `components/voice-and-audio/COMPONENT.md`,
  `components/subtitles-karaoke/COMPONENT.md`, `components/vertical-9-16-framing/COMPONENT.md`,
  `components/short-form-editing/COMPONENT.md`, `components/qc-and-render/COMPONENT.md`.
- `components/motion-studio/COMPONENT.md` (+ `templates/`, `scripts/`, `references/`).
- `components/motion-graphics/COMPONENT.md` (+ `fx.js`, `guides/` with 18 guides, `gallery/`, `test/`).
- Pack tools at `$PACK`: `scripts/` (pipeline), `lib/browser.mjs`, `examples/hello-world/`, `smoke-test/run.sh`.

## Always
Free local voices only, never clone a real voice; captions from alignment; look at stills before rendering;
a video is done only when `qc_final.py` prints OVERALL PASS; be honest about anything unchecked.
