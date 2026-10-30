---
name: lessons-from-failures
description: >-
  Hard-won rules from real code-drawn video projects that went wrong (uneven detail, regressions, inflated
  self-scores, flat art, tiny characters, robotic motion, fast narration, drifting captions, empty sound, lost
  renders, stalled agents), each as what happened, root cause, fix and rule, plus a pre-flight checklist and the
  G1-G13 delivery gates. Read at the start of every video job and before claiming a video is done.
---
# Lessons from failures

Format: **What happened -> Root cause -> Rule.** Examples are anonymised; the rules are what matter.

## A. Meta-failures (these caused most of the others)
1. **Literal execution.** The requester asked for "real-world detail" on the sky, trees and particles. Those got it;
   characters, diagrams, secondary action and lip-sync stayed at the old level, so the video looked uneven.
   *Cause:* the request was read as a checklist, not a quality bar. **Rule:** an element the requester stresses sets
   the floor for every element. Write an "improve beyond the brief" section and run the equal-attention audit (G9).
2. **Regression.** A new video applied only the latest lesson (copying a reference's minimal style) and dropped
   detail, motion and sound that earlier videos had; a solved lip-sync method quietly went back to a cheaper one.
   *Cause:* no cumulative rulebook loaded at the start. **Rule:** lessons are added, never substituted. Every job
   starts with a carry-forward list and is compared against the best frames of ALL previous videos (G8).
3. **Inflated self-scores, waived gates.** Every shot self-scored 4-5/5 and every automatic check passed, yet the
   requester judged it the worst version. A measured target missed (character size) and was shipped "with a
   caveat". *Cause:* scoring against one's own plan, numeric targets treated as soft. **Rule:** a gate is a gate.
   A measured miss means redraw, or stop and ask BEFORE rendering. Any score below 4/5 triggers a redraw; a 4 needs
   a written reason it beats the side-by-side comparison frame.
4. **Copying a reference's surface.** A reference was mis-described as simpler than it was and the plan aimed low.
   **Rule:** reverse-engineer references with measurements; keep only what beats the current standard
   (adopt / already better / reject). Outperform, never just match.

## B. Visual failures
5. **Flat colour-block art** (a ~10-shape character, 2-colour backgrounds, rendered small and upscaled).
   **Rule:** 4-6 depth planes, material textures, motivated light, prop density (G2). Never upscale or duplicate
   frames; review at full size before phone size.
6. **Characters too small** (15-49% of frame height). **Rule:** mid shots >= 55% of frame height, close-ups >= 75%,
   measured on every shot still. If the layout cannot fit, change the layout, not the target.
7. **Off or inconsistent characters** (one body palette-swapped for a whole cast, mitten hands, floating ankles).
   **Rule:** model sheets, one shared rig, black-silhouette test, constructed joints, planted feet.
8. **Plain diagrams and secondary scenes.** **Rule:** diagram shots get the same rubric (textured paper, inked shaded
   icons, margin props). The weakest shot sets the video's quality: lift the 3 weakest before rendering.
9. **Planned secondary actions silently dropped.** **Rule:** every blueprint action is a checklist item, verified in
   a motion strip, or explicitly reported as cut with the reason.

## C. Motion and editing
10. **Wrong motion density both ways:** constant sine wobble (floaty and cheap) or 78% static frames (dead); draw-on
    transitions at every cut leaving empty frames. **Rule:** hold-and-snap posing with anticipation, overshoot and
    settle plus gentle ambient life; hard cuts by default; framediff passes; never a near-blank frame at a cut.
11. **Metronomic, template editing:** a cut every 3.27 s, one layout for hundreds of shots, random kinetic words,
    one SFX per cut from a small rotation. **Rule:** cut 0-0.15 s before the key word, vary shot length 0.7-5 s,
    ~10 layouts, on-screen text carries information, SFX sit on actions, not on a grid.

## D. Voice, lip-sync and subtitles
12. **Poor lip-sync** driven by loudness or spelling. **Rule:** phoneme forced alignment mapped to ~10 visemes,
    M/B/P closed, 1-frame lead, rest within 100 ms; only the speaker's mouth moves.
13. **Narration too fast** (TTS speed 1.18 + atempo -> 182 wpm overall, 249 wpm while speaking). **Rule:** speed 1.0,
    no atempo, cut words to fit. 155-168 wpm overall, ceiling 172, speaking rate <= 195, pauses 8-15% measured
    acoustically. Around 161-165 wpm was the best-received pace.
14. **Estimated word timing** (words spread by length, captions drifted). **Rule:** align every word (MMS_FA here),
    >= 97% matched, karaoke in a fixed lower safe zone that never covers a face.

## E. Sound
15. **Mechanical or empty sound** (6 rotating SFX at fixed gain, squashed mix LRA 1.4; or no SFX at all). **Rule:**
    ambience bed per location, foley on meaningful actions, music ducked 12-15 dB under voice, -14 +/-0.5 LUFS,
    TP <= -1.5 dBTP, LRA 3-5 LU.

## F. Process and infrastructure
16. **Lost renders** after machine resets (output folders, shared modules and a venv vanished). **Rule:** render in
    parts, save each verified part inside the project, keep PROGRESS.md current with the resume command; on resume
    redo only what is missing; `free -h` first, one heavy process at a time, lower threads under 4 GB free.
17. **Agent stalls unnoticed** (~20 minutes frozen). **Rule:** periodic check; if log and session have not advanced in
    10 minutes, inspect, stop and resume the same session from PROGRESS.md.
18. **Wrong baseline** (compared with review stills because finished frames were missing). **Rule:** keep a
    `best_frames/` library from every delivered video.
19. **Caveats instead of fixes.** **Rule:** if a weak spot is fixable within budget, fix it before delivery; report
    only what is genuinely out of scope, with an offer to fix.
20. **Browser that never navigates.** A managed/enterprise Chrome (policies under `/etc/opt/chrome/policies`) aborted
    every navigation, so renders hung. **Rule:** `bash install.sh verify` renders a real test page; if the system
    browser fails, use the pinned chrome-headless-shell (`bash install.sh --with-chrome`).

# Pre-flight checklist
- [ ] Load `video-production-standard`, this skill, `motion-studio`, `qc-and-render`.
- [ ] Write the improve-beyond-the-brief section and the carry-forward list.
- [ ] Copy the best previous frames into `review/best_frames/`.
- [ ] Put numeric targets in PROGRESS.md: duration, wpm, character size, LUFS, framediff, shot count and length.
- [ ] Free voice only, original characters and script, nothing written outside the project folder.
- [ ] Restart safety: PROGRESS.md, parts plan, `free -h`, disk space, own idle processes stopped.
- [ ] `bash $PACK/install.sh verify` passes.

# Quality gates (pass/fail, before delivery)
| # | Gate | Measurable target |
|---|---|---|
| G1 | Script | Original. Hook in 0-2 s. One idea per shot. Facts checked, uncertainty stated. |
| G2 | World detail (every background, diagrams too) | Texture, light, depth (4-6 planes), density each >= 4/5, else redraw. Ambient life present. |
| G3 | Character size | Hero >= 55% of frame height in mids, >= 75% in close-ups, measured on every shot still. |
| G4 | Character craft | Silhouette test, model sheet in use, constructed joints, planted feet, expressions readable at 360x640. |
| G5 | Motion | framediff PASS (no static >= 0.75 s, no full-screen flash, no near-blank cut). 5+ strips inspected. Blueprint actions visible or reported. |
| G6 | Voice and lip-sync | 155-168 wpm (<= 172), speaking rate <= 195, pauses 8-15%. Speed 1.0, no atempo. Phoneme visemes, M/B/P closed. |
| G7 | Sound | -14 +/-0.5 LUFS, TP <= -1.5 dBTP, LRA 3-5. Ambience everywhere, foley on actions, music 12-15 dB under voice. |
| G8 | Beat-previous | Side-by-side with `best_frames/`; any shot that loses is redrawn. |
| G9 | Equal-attention audit | Every element 1-5; lowest >= 4; none more than 1 below the highest. |
| G10 | Subtitles and text | >= 97% words aligned; safe zone, never on faces; cards <= 3 real words. `subtitle_qc.mjs` PASS. |
| G11 | Technical | Native resolution and fps, full decode, 0 black/blank frames, small copy made. `qc_final.py` PASS. |
| G12 | Weakest-3 lift | The 3 lowest shots identified and improved before the final render. |
| G13 | Report | Model/effort, usage numbers with reset times in the owner's zone, honest weak spots, temp files cleaned, PROGRESS.md final. |
