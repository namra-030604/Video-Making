---
component: video-production-standard
description: >-
  End-to-end standard for short narrated videos drawn entirely in code (explainers, stories, history or science
  shorts, product explainers; 9:16 or 16:9). Use for any new video, a redo or a fix pass. Covers the brief upgrade,
  script, frame-by-frame blueprint, world art, characters, motion, phoneme lip-sync, sound, karaoke subtitles,
  measurable stage gates with automatic redraw, restart-safe rendering and the final report. Pair it with
  motion-studio (render contract, FX), motion-graphics (effect recipes) and qc-and-render (gates).
---
# Video production standard

Every new video must beat all previous ones. Lessons accumulate: a new lesson is added and never replaces an
earlier one. The failure history behind each rule is in the `lessons-from-failures` component; read it once per job.
`PACK` = the folder this repo was cloned into. Pipeline commands are in the `qc-and-render` component.

## 0. Restart safety (before anything)
- Create `PROGRESS.md` in the project folder: stage, done, next, the exact resume command, the agent session id
  and the numeric targets. Update it after every finished part (the pack scripts append to it automatically).
- On (re)start, read PROGRESS.md and the existing outputs; redo only what is missing.
- Before heavy work run `free -h` and `df -h`. Stop only your OWN idle ffmpeg/Chrome/node leftovers. One heavy
  process at a time. Lower `render.threads` if less than 4 GB is free (render.mjs refuses a part under 800 MB).
- Render in parts (`render.part_frames`), verify each part, delete large intermediates after verification.
- Keep every asset and output inside the project folder; treat reference projects as read-only.

## 1. Upgrade the brief (write it into PLAN.md)
1. **Bar:** restate the request as a quality bar. An element the requester stresses becomes the floor for EVERY element.
2. **Element sweep:** one line per element on how it reaches the bar: backgrounds, diagrams, characters, faces,
   hands and feet, props, particles, ambient life, motion, secondary action, camera, transitions, lip-sync, voice
   pace, sound, subtitles, typography, hook and ending.
3. **Carry-forward list:** every past win this video must keep (voice and pace, karaoke style, detail level, motion
   style, lip-sync method, ambience beds ...).
4. **Extras:** at least 3 improvements nobody asked for that the requester would want.
5. **Baseline:** copy the best finished frames of previous videos into `review/best_frames/`.
6. **References:** measure each reference and list *adopt / already better / reject*. Copy techniques, never
   characters, images or text. Aim to outperform the reference, not match it.

## 2. Stage 1: Script (see `script-writing`)
- Original text, hook in the first 0-2 s, one idea per sentence, an ending that mirrors the opening.
- Facts checked in FACTS.md; uncertainty stated on screen or in narration.
- Voice: free voices only (default Kokoro `af_heart`, speed 1.0, no atempo). Fit the duration by editing words,
  never by speeding up the voice.
- Measure after TTS (`audio/voice_meta.json`): 155-168 wpm overall (hard ceiling 172), speaking rate <= 195 wpm,
  pauses 8-15%.
- Word timing: `align_words.py` (MMS_FA forced alignment), >= 97% of words matched. The MMS_FA weights are CC-BY-NC 4.0 (non-commercial); see CREDITS.md.
- **Gate:** pace and match targets met; the hook reads in 2 s.

## 3. Stage 2: Frame-by-frame blueprint (FRAMES.md + shot_plan.json)
For every shot: time range locked to aligned words (cut 0-0.15 s before the key word), the spoken line, the one
dominant idea, layout, background, characters with pose and expression, props, fore/mid/background, particles
and ambient life, main action with its easing, secondary actions, camera move, transition (hard cut by default),
SFX/foley/ambience and on-screen text (3 words or fewer, real words only).
- Vary shot length (0.7-5 s, never a metronomic grid); about 10 layouts; never the same framing twice in a row.
- Vertical frames: a top card zone, a hero zone and a lower subtitle safe zone, no faces in the subtitle zone.
- Explainers: graphic/diagram shots get >= 30% of runtime and must be lively (arrows, ticks, insets, labels).
- **Gate:** every shot literally shows its sentence; every blueprint action becomes a stage-5 checklist item.

## 4. Stage 3: World art (before characters)
Each location = 4-6 separate planes (sky, far, mid, decor, fore, near) at native resolution.
- Materials: grain, ripples, cracks and chips, wood grain, leaf clusters with light and shadow sides, water
  reflections, cloth weave, paper fibre (see `motion-graphics` guides: halftone, ink-watercolor, light-and-glow).
- Light: one motivated key (sun, lamp, fire, window) setting shadows, rim light and grade; atmospheric perspective.
- Life: dust motes, pollen, embers, drifting clouds, rippling water, flicker, moving foliage.
- **Gate (auto-redraw):** score each background 1-5 on texture, light, depth and prop density, full size and on a
  270x480 sheet next to `best_frames/`. Any score below 4 = redraw before stage 4.

## 5. Stage 4: Characters (when the video has them)
- One model sheet per character (front, 3/4, side, close-up, ~12 expressions, ~10-viseme mouth chart, hand poses,
  palette, fixed spec paragraph). One shared rig; never redesign per scene.
- Original designs; each role has a distinct silhouette that passes the black-silhouette test.
- Construction: shoulder-elbow-wrist paths, separated fingers, planted feet with contact shadows.
- **Size:** hero >= 55% of frame height in mid shots, >= 75% in close-ups, measured from bounding boxes.

## 6. Stage 5: Compose, motion, lip-sync, sound, subtitles
- **Stills first:** `node $PACK/scripts/stills.mjs --project . --n <shots> --scan`; build a 360x640 phone sheet;
  score every shot; below 4 = redraw; lift the 3 weakest shots even if they passed.
- **Motion:** hold-and-snap key poses with anticipation, overshoot and settle; follow-through; squash and stretch;
  one motivated eased camera move per shot with real parallax; gentle ambient life; no constant wobble, no dead holds.
- **Transitions:** hard cuts on complete frames by default; motivated dissolve/wipe/match-cut only for emphasis;
  never a near-blank frame.
- **Lip-sync:** when a mouth is visible, align phonemes (espeak-ng IPA + wav2vec2/MMS CTC forced alignment), map
  to ~10 visemes, hold >= 2 frames, blend 1-2 frames, fully close on M/B/P, open 1 frame early, rest within 100 ms.
  Only the speaker's mouth moves. Verify with per-line close-up strips against the waveform.
- **Sound** (`voice-and-audio`): ambience bed per location, foley on meaningful actions, music ducked 12-15 dB
  under the voice. -14 +/-0.5 LUFS, true peak <= -1.5 dBTP, LRA 3-5 LU.
- **Subtitles** (`subtitles-karaoke`): word-highlight karaoke from aligned times in the lower safe zone.
- **Render:** native resolution and fps, in verified parts, PROGRESS.md updated per part.

## 7. Delivery gates (all must pass; fix, do not footnote)
1. `qc_final.py` PASS: full decode, resolution, fps, duration, A/V sync, no black/blank/static stretches,
   loudness, true peak, words aligned, subtitle QC. A small copy (`render.small_height`, e.g. 720) is made.
2. `framediff.py` PASS; 5+ ten-frame strips inspected for pops, stutter and joint breaks.
3. Every blueprint action is visible in the render, or reported as cut with the reason.
4. **Equal-attention audit:** score each element 1-5; the lowest >= 4, none more than 1 below the highest.
5. A beat-previous sheet shows no shot losing to `best_frames/`.
6. If a numeric target fails, fix it; if it truly cannot be fixed within budget, stop and ask BEFORE delivering.

## 8. Running it with a coding agent
- Run long renders in the background with a log; check it periodically. If neither the log nor the agent session
  has advanced for 10+ minutes, inspect, stop it, and resume from PROGRESS.md.
- Never change the agent's global config, never use bypass/"danger"/full-auto modes, never add keys or plugins
  without the owner's OK. Iterate on the same session with concrete numbered feedback.

## 9. Final report (every job)
Deliver the video (plus the small copy), contact sheet and qc_final.json with a plain-language summary, the honest
remaining weak spots and an offer to fix them. Include the model and effort used and any usage-limit numbers you
can read, with reset times in the owner's time zone. Finalize PROGRESS.md and confirm temp files were cleaned.
