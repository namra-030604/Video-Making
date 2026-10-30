---
name: short-form-editing
description: >-
  Editing techniques for short vertical videos and launch/explainer reels: cold-open hook, top hook bar, keyword
  colour captions, hard payoff cuts, pacing rules, plus generalized recipes for turning a project's own code or
  website into a launch video and for explainer modes (kinetic text, diagram, quote card, map/timeline). Use when
  cutting existing footage into Shorts or designing a short code-drawn reel.
---
# Short-form editing

## Cutting existing footage (talk, interview, podcast, gameplay)
Only use footage you have the right to use; keep every claim in context.
1. **Find the moment:** transcribe (align or any free ASR), mark the strongest 20-45 s segment: a conflict, a
   surprising answer, or a clear before/after.
2. **Cold open:** start on the most intense 1-3 s (the punchline question or the reaction), then cut back to the
   setup. The first frame must already be moving and readable without sound.
3. **Top hook bar:** a solid bar in the top card zone with 3-7 words that frame the question ("He did not expect
   this answer"). Keep it on screen the whole clip; it must be true to the content.
4. **Captions:** karaoke captions (`subtitles-karaoke`) with 1-2 keywords per line in an accent colour (yellow on
   white is common); heavy sans, stroke or backing box, inside the caption safe zone.
5. **Cut rhythm:** remove breaths, fillers and pauses > 0.3 s (jump cuts are fine); a visual change every 2-4 s
   (punch-in 110-120% zoom, angle switch, B-roll, text pop).
6. **Payoff:** hard cut right after the payoff line; no fade-out, no outro. Loop-friendly endings (the last line
   leads back to the first frame) help replays.
7. **Reframe** with `vertical-9-16-framing`; mix with `voice-and-audio` (dialogue -14 LUFS, music under -12 dB).
8. **Vary a batch:** when cutting several clips, rotate hook types (question, claim, reaction, number), bar colours
   and caption styles so they do not look templated.

ffmpeg building blocks:
- cut: `ffmpeg -ss 12.4 -to 41.0 -i in.mp4 -c:v libx264 -crf 18 -c:a aac seg.mp4`
- punch-in: `-vf "crop=iw/1.15:ih/1.15,scale=1080:1920"`
- hook bar + text: `drawbox=x=0:y=150:w=iw:h=190:color=black@0.85:t=fill,drawtext=fontfile=Inter.ttf:text='...':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=205`
- or draw everything (bar, captions, zooms) in a canvas page over `MS.seekVideo` frames and render with the pack.

## Launch video from a project's own code
1. Read the project: README, package names, main screens or CLI output, real numbers (tests, speed, size).
2. Pull 3-5 true facts and 1 visual signature (brand colour, logo shape, a key UI screen recreated in canvas or a
   real screenshot you made yourself).
3. 15-30 s structure: problem (1 line) -> product name reveal -> 3 feature beats (each a UI mock or code snippet
   typing in) -> result number -> call to action (URL or repo).
4. Music-led: use `motion-studio` (beat sheet, cuts on beats, synthesized bed); captions optional.
5. Write share copy: one-line post, 3 hashtags max, alt text describing the video.

## Explainer modes (pick one per video, mix sparingly)
| Mode | When | Build with |
|---|---|---|
| Kinetic text | ideas, quotes, lists | `motion-graphics/guides/kinetic-text.md`, `text-mask-reveal.md` |
| Diagram | systems, processes, cause-effect | `stroke-draw-handwriting.md`, `shape-morph.md`, `transitions.md` |
| Quote card | one strong sentence + attribution | `glass-cards.md`, `light-and-glow.md` |
| Map / timeline | history, travel, sequences | `map-and-timeline.md` (optional `--with-maps`), `camera-and-parallax.md` |
| Data | numbers, comparisons | `charts.md`, `counters.md` |
| Character cartoon | stories | code-drawn characters in canvas; see `video-production-standard` |

## Pacing checklist
- Hook visible and audible in < 2 s; something moves in frame 1.
- No static stretch > 0.75 s (`framediff.py`), no full-screen flashing.
- Text readable on a phone: >= 56 px at 1080 wide, max ~6 words per on-screen card.
- End within 0.5 s after the payoff.
