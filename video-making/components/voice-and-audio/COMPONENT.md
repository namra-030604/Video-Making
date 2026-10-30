---
component: voice-and-audio
description: >-
  Free, local narration and sound for code-made videos: Kokoro TTS (Apache-2.0 weights, voice af_heart, speed 1.0)
  with an espeak-ng fallback, MMS_FA word alignment, a synthesized music bed and SFX cues (swish, pop, tick,
  impact, riser) placed on words or times, voice ducking, and two-pass loudness to -14 LUFS / true peak -1.5 dBTP.
  Lists CC0/CC-BY music and SFX sources and Piper as an alternative engine. Use for any voice-over, music or mix work.
---
# Voice and audio

Free voices only. Never clone a real person or the user's own voice; no paid TTS.

## 1. Voice: `scripts/make_voice.py`
```bash
PY=$(cat $PACK/.vsp-state/python)
$PY $PACK/scripts/make_voice.py --project .            # Kokoro (default)
$PY $PACK/scripts/make_voice.py --project . --engine espeak   # robotic fallback, no model needed
```
`project.json`:
```json
"lines": ["One sentence per line.", "Each line becomes one WAV."],
"voice": { "engine": "kokoro", "voice": "af_heart", "speed": 1.0, "lang": "en-us",
           "lead_s": 0.15, "gap_s": 0.25, "tail_s": 0.45 }
```
Writes `audio/line_NN.wav`, `audio/voice.wav` and `audio/voice_meta.json` (offsets, durations, wpm overall and
while speaking, pause fraction). Skips work when lines/settings are unchanged (`--force` to redo).
- Keep `speed` at 1.0 and never time-stretch (atempo). Fit the duration by editing words.
- Pace target for long videos: 155-168 wpm overall, ceiling 172 (`qc_final.py` enforces 150-172 above 15 s).
- Other Kokoro voices ship in `voices-v1.0.bin` (e.g. `af_bella`, `am_adam`, `bf_emma`, `bm_george`); listen first.

## 2. Alignment: `scripts/align_words.py`
torchaudio MMS_FA (Meta's multilingual forced-alignment model, ~1.2 GB, cached). Writes `align/words.json`;
fails under 97% matched. Words are romanised for the aligner, so digits should be written out in `lines`
("twenty twenty-six", not "2026").

**License warning:** the MMS_FA weights are published under **CC-BY-NC 4.0 (non-commercial)**. Fine for personal,
learning and non-commercial videos. For commercial work, replace the alignment step with an aligner whose license
allows it (not included in this pack, untested) and keep the same `align/words.json` format.

## 3. Music, SFX and loudness: `scripts/make_audio.py`
```json
"audio": { "lufs": -14, "true_peak": -1.5, "bed": "pad", "bed_level_db": -30, "pad_root_hz": 110, "seed": 3,
           "sfx": [ { "word": "hello", "kind": "swish", "gain": 0.06 }, { "at": 2.4, "kind": "impact", "gain": 0.1 } ] }
```
- `bed`: `pad` (a soft synthesized chord pad with slow movement) or `none`. Ducked under the voice.
- SFX `kind`: `swish | pop | tick | impact | riser`; place by `word` (first aligned occurrence) or `at` seconds.
- Loudness: ffmpeg `loudnorm` measure -> linear gain -> re-measure loop, then a true-peak limiter; 48 kHz stereo.
  Result in `audio/loudness.json`; `qc_final.py` re-measures the final mp4.
- Music-heavy motion pieces: `video-making/components/motion-studio/scripts/synth_audio.py` (BPM bed, drums, crash on cuts) and
  `mix.py` (ducking + loudness + mux).
- Targets: -14 +/-0.5 LUFS integrated, TP <= -1.5 dBTP, LRA 3-5 LU, music 12-15 dB under the voice.

## 4. Alternatives (documented, not installed)
- **Piper** (rhasspy/piper, MIT, archived; successor OHF-Voice/piper1-gpl is GPL-3.0). Fast CPU voices. Check each
  voice's model card: some are public domain/CC0, some are non-commercial (CC BY-NC) or unclear. Render a line to
  WAV, put it in `audio/line_NN.wav` and `audio/voice.wav`, then run the alignment and mix steps as usual.
- **espeak-ng** (GPL-3.0): installed with the Python stack via espeakng-loader; intelligible but robotic.

## 5. Free music and SFX sources (check each file's own license, record it in assets/CREDITS.md)
- Freesound.org: filter by **CC0** (CC BY needs credit; avoid CC BY-NC for commercial work).
- Openverse (openverse.org): audio search, filter CC0 / public domain.
- Wikimedia Commons: audio with per-file licenses (CC0, PD, CC BY, CC BY-SA).
- OpenGameArt.org: many CC0 SFX and loops (licenses vary per item).
- Kenney.nl audio packs: CC0.
Prefer synthesized sound first: it has no license risk and is always frame-exact.
