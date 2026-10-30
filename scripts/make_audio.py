#!/usr/bin/env python3
"""make_audio.py - license-free sound design + broadcast loudness for the narration.

Everything here is synthesized in code (no samples), so there is no music licence risk:
  * an ambient pad bed (soft chord + filtered noise) ducked under the voice,
  * SFX cues ("swish", "pop", "tick", "impact", "riser") placed at a time or on an aligned word,
  * two-pass ffmpeg loudnorm to the target (default -14 LUFS integrated, true peak <= -1.5 dBTP),
    then a measurement loop that nudges gain with a limiter until it is in range.

project.json -> "audio": {"lufs": -14, "true_peak": -1.5, "bed": "pad"|"none", "bed_level_db": -30,
                          "sfx": [{"at": 1.2, "kind": "swish"}, {"word": "video", "kind": "pop"}]}
Outputs: audio/mix.wav (48 kHz stereo), audio/loudness.json
Usage: python scripts/make_audio.py --project DIR [--force]
"""
import argparse, json, os, re, subprocess, sys, hashlib
import numpy as np
import soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
from vsp_common import load_project, note, vget

SR = 48000

def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    return json.loads(re.search(r'\{\s*"input_i".*?\}', r.stderr, re.S).group())

def synth(n, cfg, words, voice):
    t = np.arange(n) / SR
    rng = np.random.default_rng(int(vget(cfg, "audio.seed", 7)))
    def noise(smooth):
        x = rng.standard_normal(n).astype(np.float32)
        return np.convolve(x, np.ones(smooth, np.float32) / smooth, "same")
    bed = np.zeros(n, np.float32)
    if vget(cfg, "audio.bed", "pad") == "pad":
        root_hz = float(vget(cfg, "audio.pad_root_hz", 110.0))
        chord = sum(w * np.sin(2 * np.pi * root_hz * r * t) for r, w in ((1, 1), (1.5, .35), (2, .25), (2.52, .15)))
        swell = .6 + .4 * np.sin(2 * np.pi * .09 * t) ** 2
        fade = np.clip(t / 0.6, 0, 1) * np.clip((t[-1] - t) / 0.8, 0, 1)
        bed = (chord * swell * 0.25 + 0.6 * noise(700)) * fade
        bed = bed / (np.max(np.abs(bed)) + 1e-9) * 10 ** (float(vget(cfg, "audio.bed_level_db", -30)) / 20)
    sfx = np.zeros(n, np.float32)
    def hit(at, kind):
        x = np.maximum(t - at, 0); on = t >= at
        if kind == "swish":   return on * np.exp(-x / .18) * noise(30) * np.sin(np.pi * np.clip(x / .3, 0, 1)) * 2.5
        if kind == "pop":     return on * np.exp(-x / .05) * np.sin(2 * np.pi * (520 - 900 * x) * x)
        if kind == "tick":    return on * np.exp(-x / .012) * np.sin(2 * np.pi * 2400 * x)
        if kind == "impact":  return on * np.exp(-x / .25) * (np.sin(2 * np.pi * (70 - 30 * x) * x) + .4 * noise(12))
        if kind == "riser":   return (t < at) * np.clip(1 - (at - t) / .8, 0, 1) ** 2 * noise(6) * 0.8
        raise ValueError("unknown sfx kind " + kind)
    for cue in vget(cfg, "audio.sfx", []) or []:
        at = cue.get("at")
        if at is None and "word" in cue:
            m = next((w for w in words if w["word"].lower() == cue["word"].lower()), None)
            if not m: print("WARNING: sfx word not found:", cue["word"]); continue
            at = m["start"] - 0.03
        sfx += float(cue.get("gain", 0.08)) * hit(float(at), cue.get("kind", "swish"))
    # duck the bed under speech (about 12-15 dB below the voice)
    env = np.convolve((np.abs(voice) > 0.01).astype(np.float32), np.ones(int(SR * .12)) / int(SR * .12), "same")
    bed *= 1 - 0.5 * np.clip(env, 0, 1)
    return bed, sfx

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--project", default="."); ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    root, cfg = load_project(a.project)
    meta = json.loads((root / "audio/voice_meta.json").read_text())
    wj = root / "align/words.json"; words = json.loads(wj.read_text())["words"] if wj.exists() else []
    target_i = float(vget(cfg, "audio.lufs", -14)); target_tp = float(vget(cfg, "audio.true_peak", -1.5))
    key = hashlib.sha256((meta["key"] + json.dumps(cfg.get("audio", {}), sort_keys=True)).encode()).hexdigest()[:16]
    lj = root / "audio/loudness.json"
    if not a.force and lj.exists() and json.loads(lj.read_text()).get("key") == key and (root / "audio/mix.wav").exists():
        print("audio: up to date, skipped"); return
    v, sr = sf.read(root / "audio/voice.wav", dtype="float32")
    if sr != SR:
        n = int(round(len(v) * SR / sr)); v = np.interp(np.linspace(0, len(v) - 1, n), np.arange(len(v)), v).astype(np.float32)
    bed, sfx = synth(len(v), cfg, words, v)
    raw = np.tanh((v + bed + sfx) * 0.95).astype(np.float32)
    raw_path = root / "audio/raw_mix.wav"; sf.write(raw_path, np.stack([raw, raw], 1), SR)
    m = measure(raw_path)
    flt = (f"loudnorm=I={target_i}:TP={target_tp - 0.5}:LRA=7:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
           f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    out = root / "audio/mix.wav"; gain = 0.0
    for attempt in range(5):
        af = flt + (f",volume={gain:.2f}dB" if gain else "") + f",alimiter=limit={10 ** ((target_tp - 0.6) / 20):.4f}:level=false:attack=1:release=50"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw_path), "-af", af, "-ar", str(SR), "-ac", "2", str(out)], check=True)
        r = measure(out); I, TP = float(r["input_i"]), float(r["input_tp"])
        print(f"loudness attempt {attempt + 1}: {I:.2f} LUFS, {TP:.2f} dBTP (gain {gain:+.2f} dB)")
        if abs(I - target_i) <= 0.5 and TP <= target_tp: break
        gain += target_i - I
    else:
        sys.exit(f"FAIL: could not reach {target_i} LUFS / {target_tp} dBTP")
    raw_path.unlink()
    lj.write_text(json.dumps({"key": key, "integrated_lufs": I, "true_peak_dbtp": TP, "lra": float(r["input_lra"]), "target_lufs": target_i, "target_true_peak": target_tp}, indent=2) + "\n")
    note(root, f"audio: mix.wav {I:.2f} LUFS, {TP:.2f} dBTP")

if __name__ == "__main__":
    main()
