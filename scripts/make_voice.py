#!/usr/bin/env python3
"""make_voice.py - narrate project.json "lines" with a FREE local voice.

Default engine: Kokoro (kokoro-onnx, Apache-2.0 weights), voice af_heart, speed 1.0.
Never speed the voice up to fit a duration - edit the words instead.
Fallback engine (only if Kokoro is unavailable, and it says so): espeak-ng (robotic but free).

Outputs (inside the project):
  audio/line_NN.wav      one file per line (24 kHz mono)
  audio/voice.wav        all lines with lead/gap/tail silence
  audio/voice_meta.json  offsets, durations, wpm, pause fraction, engine used

Usage: python scripts/make_voice.py --project DIR [--engine kokoro|espeak] [--force]
"""
import argparse, hashlib, json, re, shutil, subprocess, sys
import numpy as np
import soundfile as sf
sys.path.insert(0, __import__("os").path.dirname(__file__))
from vsp_common import load_project, models_dir, note, vget

WORD = r"[\w]+(?:'[\w]+)?"

def kokoro_tts(lines, voice, speed, lang):
    from kokoro_onnx import Kokoro
    m = models_dir()
    k = Kokoro(str(m / "kokoro-v1.0.int8.onnx"), str(m / "voices-v1.0.bin"))
    out = []
    for line in lines:
        audio, sr = k.create(line, voice=voice, lang=lang, speed=speed)
        a = np.asarray(audio, dtype=np.float32)
        out.append((a, sr))
    return out

def espeak_tts(lines, tmp):
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        sys.exit("No TTS available: Kokoro failed and espeak-ng is not installed.")
    out = []
    for i, line in enumerate(lines):
        wav = tmp / f"espeak_{i}.wav"
        subprocess.run([exe, "-v", "en-us", "-s", "165", "-w", str(wav), line], check=True)
        a, sr = sf.read(wav, dtype="float32"); wav.unlink()
        if a.ndim > 1: a = a.mean(1)
        # resample to 24 kHz with ffmpeg-free linear interpolation (fine for a fallback)
        if sr != 24000:
            n = int(len(a) * 24000 / sr); a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32); sr = 24000
        out.append((a, sr))
    return out

def trim(a, sr, thresh=0.004):
    """Trim leading/trailing near-silence but keep 30 ms of air."""
    idx = np.where(np.abs(a) > thresh)[0]
    if not len(idx): return a
    pad = int(0.03 * sr)
    return a[max(0, idx[0] - pad): min(len(a), idx[-1] + pad)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--engine", choices=["kokoro", "espeak"], default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    root, cfg = load_project(a.project)
    lines = [l.strip() for l in cfg["lines"] if l.strip()]
    voice = vget(cfg, "voice.voice", "af_heart"); speed = float(vget(cfg, "voice.speed", 1.0)); lang = vget(cfg, "voice.lang", "en-us")
    lead = float(vget(cfg, "voice.lead_s", 0.15)); gap = float(vget(cfg, "voice.gap_s", 0.25)); tail = float(vget(cfg, "voice.tail_s", 0.35))
    engine = a.engine or vget(cfg, "voice.engine", "kokoro")
    key = hashlib.sha256(json.dumps([lines, voice, speed, lang, lead, gap, tail, engine]).encode()).hexdigest()[:16]
    (root / "audio").mkdir(exist_ok=True)
    meta_path = root / "audio/voice_meta.json"
    if not a.force and meta_path.exists() and json.loads(meta_path.read_text()).get("key") == key and (root / "audio/voice.wav").exists():
        print("voice: up to date, skipped"); return
    if speed != 1.0:
        print(f"WARNING: voice speed {speed} != 1.0. The standard is speed 1.0; edit words to fit time instead.")
    used = engine
    if engine == "kokoro":
        try:
            parts = kokoro_tts(lines, voice, speed, lang)
        except Exception as e:  # honest fallback
            print(f"Kokoro unavailable ({e}); FALLING BACK to espeak-ng. Re-run install.sh to fix Kokoro.")
            parts = espeak_tts(lines, root / "audio"); used = "espeak-ng (fallback)"
    else:
        parts = espeak_tts(lines, root / "audio")
    sr = parts[0][1]
    samples = [np.zeros(round(lead * sr), np.float32)]; cursor = lead; offsets = []; durs = []
    for i, (p, _) in enumerate(parts, 1):
        p = trim(p, sr)
        sf.write(root / f"audio/line_{i:02d}.wav", p, sr)
        offsets.append(cursor); durs.append(len(p) / sr); samples.append(p); cursor += len(p) / sr
        if i < len(parts):
            samples.append(np.zeros(round(gap * sr), np.float32)); cursor += gap
    samples.append(np.zeros(round(tail * sr), np.float32))
    v = np.concatenate(samples); sf.write(root / "audio/voice.wav", v, sr)
    words = sum(len(re.findall(WORD, l)) for l in lines); total = len(v) / sr; speech = sum(durs)
    meta = {"key": key, "engine": used, "voice": voice, "speed": speed, "lines": lines, "line_durations": durs, "offsets": offsets,
            "duration": total, "word_count": words, "speech_duration": speech,
            "wpm_overall": words / total * 60, "wpm_speech": words / speech * 60, "pause_fraction": 1 - speech / total}
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    note(root, f"voice: {len(lines)} lines, {total:.2f}s, {meta['wpm_overall']:.0f} wpm overall, engine {used}")
    print(json.dumps({k: (round(x, 3) if isinstance(x, float) else x) for k, x in meta.items() if k not in ("lines",)}, indent=2))

if __name__ == "__main__":
    main()
