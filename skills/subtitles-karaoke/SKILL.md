---
name: subtitles-karaoke
description: >-
  Word-by-word karaoke subtitles drawn on the canvas from forced-aligned word times (align/words.json), kept in a
  measured safe zone and checked automatically (subtitle_qc.mjs: safe-area every 0.1 s, word onset within one
  frame). Use whenever a narrated video needs captions, keyword highlights or burned-in subtitles.
---
# Karaoke subtitles

Captions must be the script's own words, timed by alignment, never re-typed and never estimated from word length.

## Data
`python3 $PACK/scripts/align_words.py --project .` writes `align/words.json`:
`{matched_fraction, words: [{line_index, word, start, end, score}]}` (times in seconds on the final timeline,
including the voice lead-in). The alignment model (MMS_FA) is CC-BY-NC 4.0: non-commercial use only. It fails if fewer than 97% of words align. The renderer passes these words to your
page through `window.init({project, words, meta})` before the first frame.

## Drawing rules (see `examples/hello-world/index.html`, function `subtitles`)
- Show the current script line only (from 0.1 s before its first word to 0.3 s after its last word).
- Active word = the last word whose `start <= t`. Highlight it (colour + a small 0.12 s pop); already-spoken words
  full white; upcoming words dimmed. Uppercase heavy sans (Inter 800) with a translucent rounded backing box.
- Wrap rows to the safe width; centre the block between `safe_top` and `safe_bottom`.
- Safe zone (fractions of height/width, set in `project.json -> subtitles`): defaults `safe_top 0.70`,
  `safe_bottom 0.92`, `safe_side 0.05`. For 9:16 social video keep captions above the bottom ~8-10% (platform UI)
  and away from the right edge buttons; never over a face or the hero object.
- Size: about 34 px at 540x960 (= 68 px at 1080x1920). At least 0.8 s on screen per row.
- Keyword style for short-form: one or two information words per line in an accent colour (e.g. yellow) chosen in
  the script (`script-writing`), not random words.

## Contract for QC
`renderFrame(t)` (or `seek`) returns `{subtitleBoxes: [[x, y, w, h], ...], activeWord, activeStart}`.
`node $PACK/scripts/subtitle_qc.mjs --project .` samples every 0.1 s and fails when a box leaves the safe area, and
checks (up to 60 words) that each word becomes active within one frame of its aligned start. Results go to
`out/subtitle_qc.json`; `qc_final.py` includes them. Pages that do not return boxes get a SKIP, not a PASS.

## SRT/VTT export (for platforms that take sidecar captions)
Build cues from `align/words.json` grouped by `line_index` (start of first word, end of last word). Keep the text
identical to the script lines in `project.json`.
