---
name: script-writing
description: >-
  Write narration scripts that fit a target duration and read well aloud: words-to-seconds math at ~165 wpm, a
  hook in the first 1-2 seconds, one idea per line, spelled-out numbers for alignment, keyword picks for caption
  highlights, and a beat list that maps each line to a visual. Use before generating any voice-over.
---
# Script writing

## Length math (Kokoro af_heart at speed 1.0 speaks ~160-170 wpm including short pauses)
| Target | Words (at 165 wpm) |
|---|---|
| 15 s | ~40 |
| 30 s | ~80 |
| 45 s | ~120 |
| 60 s | ~165 |
| 90 s | ~245 |
`words = seconds * 165 / 60`, then subtract ~2 words per line break (each line adds `gap_s` 0.25 s of silence).
After `make_voice.py`, read `audio/voice_meta.json -> wpm_overall` and duration. Too long: cut words. Too short:
add a concrete detail. Never speed the voice up or time-stretch it to fit.

## Structure for short-form (15-60 s)
1. **Hook (0-2 s, <= 12 words):** a surprising claim, a question the viewer wants answered, or the end result
   shown first. No greeting, no "in this video".
2. **Setup (one or two lines):** the context needed to care.
3. **Body:** 3-5 beats, one idea per line, each with its own visual.
4. **Payoff:** answer the hook in the last 15%; end on a strong line, not "thanks for watching".
For longer explainers repeat hook -> beats -> payoff per section and keep a mini-hook every ~20 s.

## Line rules
- One sentence per `lines` entry, 6-16 words. Short words, active verbs, present tense.
- Write numbers, symbols and abbreviations as spoken ("forty percent", "A I" or a word, "and" not "&"): the aligner
  only matches letters.
- Avoid tongue twisters and lists of names; read every line aloud once.
- Mark 1-2 highlight words per line (nouns/numbers that carry the meaning) for keyword-coloured captions.
- Facts: only claims you can source; keep a `sources.md` next to the project for anything non-obvious.

## Beat list (write before any visuals)
```
| # | line (spoken) | seconds | visual (what moves) | caption keyword | sfx |
```
Every beat needs a visual change at least every 2-3 s; this list becomes `beats.json` or the scene code.

## Visual safe zones while writing on-screen text
Title/hook text sits in the top card (8-25% height in 9:16), captions in 70-90%; on-screen text <= 6 words and
must not repeat the caption word for word.
