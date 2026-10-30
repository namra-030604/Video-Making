# Self-critique loop (do this BEFORE showing anyone the video)

1. Render the contact sheet: `python3 $PACK/skills/motion-studio/scripts/contact_sheet.py --project . --every-beat --mid` -> `out/contact_sheet.png`
   (one frame per beat, labelled with time, beat id and the planned action). Open the PNG and LOOK at it.
2. Score every axis 1-10 in `out/scorecard_round<N>.json` (copy `out/scorecard_template.json`):

| Axis | 10 looks like | Typical fails (score <= 6) |
|---|---|---|
| readability | every word readable at phone size for >= 0.8 s, strong contrast, inside safe margins | text over busy art, too small (< 48 px at 1080p), on screen < 0.5 s |
| motion_quality | eased (slow-in/out, elastic, bounce, squash & stretch), overlapping action, nothing linear | linear slides, everything fades, robotic constant speed, dead/static frames |
| brand_accuracy | brand colours, logo, product name, UI theme consistent in every frame | off-palette colours, mixed UI themes, wrong name/claims |
| sound_sync | every click/whoosh/pop on the exact frame of its action, music lands on cuts, voice clear | sfx early/late, cuts between beats, music masks voice |
| composition | clear hero per beat, nothing covers the title or hero object, balanced negative space, split screens aligned | clutter, title covered by cursor/flare, cramped edges, text overlapping during transitions |
| typography | mixed bold serif + sans with clear hierarchy, kinetic per word, good kerning, max 2-3 families | one flat font, centred title on gradient, widows, clipped glyphs |
| hook_strength | 0-2 s has a bold move + question/promise; viewer knows why to keep watching | slow logo fade-in, blank first second, generic title card |

3. Write the **worst 3 problems** (concrete: "2.1 click ring hides the 'Live' label", not "improve design").
4. Fix those 3, re-render the sheet, re-score. Repeat until **every axis >= 8**. Keep each round's scorecard.
5. Then also run the machine checks:
   - `node $PACK/scripts/stills.mjs --project . --check` -> determinism PASS (same t twice = same pixels, in any order).
   - `python3 $PACK/scripts/framediff.py out/final.mp4` -> no static stretches > 0.75 s, no full-screen flashes.
   - `python3 $PACK/skills/motion-studio/scripts/mix.py --measure out/final.mp4` -> integrated about -14 LUFS (+/- 1), true peak <= -1 dBTP.
   - captions: every caption string must be copied from the script (align/words.json), never re-typed.
   - transitions: the outgoing scene is masked/cleared (clip or tear mask), so text from two scenes never overlaps.
6. Only then show the result: final MP4 + contact sheet + last scorecard + CHANGELOG.md.

Honest numbers only. If an axis is still < 8 after 4 rounds, say which and why instead of claiming it passed.
