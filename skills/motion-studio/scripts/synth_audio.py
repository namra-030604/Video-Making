#!/usr/bin/env python3
"""synth_audio: original music + sound effects made in code (numpy only, seeded, 48 kHz stereo WAV).

Subcommands
  sfx   --type click|whoosh|pop|impact|riser|tick|swoosh_down --out x.wav [--seed 1]
  music --bpm 120 --duration 10 --out audio/music.wav [--seed 1] [--key A] [--hits 2.0,4.0] [--style bed|drive|chill]
        Original 4-on-the-floor bed: kick, clap on 2/4, 8th hats, bass, soft pad (i-VI-III-VII).
        --hits: times (s) of visual cuts; each gets a crash + sub drop, and the drums drop out for the
        half-beat before it, so the music LANDS on the cut. Hits are snapped to the beat grid.
  cues  --beats beats.json --out audio/sfx.wav     Builds one SFX track: every beats[].sfx {t, type, gain}
        is placed on the exact sample of its visual action (sample = round(t*48000); frame-exact at any fps).
  bed   --beats beats.json --out audio/music.wav    = music using bpm/duration/seed from beats.json and
        hits = every beat with "cut": true.
Everything is generated here, so there are no licensing questions. Keep sfx short; never mask the voice.
"""
import argparse, json, os, sys, wave
import numpy as np

SR = 48000

def write_wav(path, x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1: x = np.stack([x, x], 1)
    peak = np.max(np.abs(x)) or 1.0
    if peak > 0.99: x = x * (0.99 / peak)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())

def fft_filter(x, lo=None, hi=None):
    n = len(x); X = np.fft.rfft(x, n * 2); f = np.fft.rfftfreq(n * 2, 1 / SR); m = np.ones_like(f)
    if lo: m *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)
    if hi: m *= 1 / np.sqrt(1 + (f / hi) ** 4)
    return np.fft.irfft(X * m)[:n]

def sweep_filter(x, centers, q=1.2, block=1024):
    """time-varying band-pass via overlap-add FFT blocks; centers: array of Hz per sample"""
    hop = block // 2; win = np.hanning(block); out = np.zeros(len(x) + block); f = np.fft.rfftfreq(block, 1 / SR)
    xp = np.concatenate([x, np.zeros(block)])
    for s in range(0, len(x), hop):
        c = centers[min(s, len(centers) - 1)]; bw = c / q
        m = np.exp(-0.5 * ((f - c) / bw) ** 2)
        out[s:s + block] += np.fft.irfft(np.fft.rfft(xp[s:s + block] * win) * m) * win
    return out[:len(x)]

def env(n, a, d, curve=4.0):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-curve * np.maximum(0, t - a) / max(d, 1e-4)); return e

def sfx(kind, seed=1):
    r = np.random.default_rng(seed)
    if kind == "click":     # crisp UI click: short filtered noise tick + tiny body
        n = int(0.06 * SR); t = np.arange(n) / SR
        x = fft_filter(r.standard_normal(n), lo=2500, hi=12000) * np.exp(-t * 180) * 0.6
        x += np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 120) * 0.35
        return x
    if kind == "tick":
        n = int(0.03 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 300) * 0.5
    if kind == "pop":       # bubbly pop: fast downward pitch sweep
        n = int(0.12 * SR); t = np.arange(n) / SR; f = 900 * np.exp(-t * 25) + 250
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.05, 3) * 0.8
    if kind in ("whoosh", "swoosh_down"):   # air whoosh: noise through a sweeping band-pass, swell then fade
        n = int(0.55 * SR); t = np.arange(n) / SR
        c = 400 + 3200 * np.sin(np.pi * t / t[-1]) ** 2 if kind == "whoosh" else 3600 * np.exp(-t * 5) + 300
        x = sweep_filter(r.standard_normal(n), c, q=1.0)
        e = np.sin(np.pi * np.clip(t / t[-1], 0, 1)) ** 1.5
        L = x * e; R = np.roll(x, 40) * e   # tiny stereo spread
        return np.stack([L, R], 1) * 0.9
    if kind == "impact":    # sub boom + noise crack
        n = int(0.9 * SR); t = np.arange(n) / SR; f = 110 * np.exp(-t * 8) + 38
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.35, 3)
        x += fft_filter(r.standard_normal(n), lo=800) * env(n, 0.001, 0.08, 4) * 0.4
        return x
    if kind == "riser":     # 1 s rising noise + tone, ends on the downbeat
        n = int(1.0 * SR); t = np.arange(n) / SR
        x = sweep_filter(r.standard_normal(n), 300 + 6000 * (t / t[-1]) ** 2, q=2) * (t / t[-1]) ** 2
        x += np.sin(2 * np.pi * np.cumsum(200 + 800 * (t / t[-1]) ** 2) / SR) * (t / t[-1]) ** 3 * 0.25
        return x
    raise SystemExit(f"unknown sfx type {kind}")

def place(track, clip, t, gain=1.0):
    clip = clip if clip.ndim == 2 else np.stack([clip, clip], 1)
    s = int(round(t * SR))
    if s >= len(track): return
    e = min(len(track), s + len(clip)); track[s:e] += clip[:e - s] * gain

NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
def hz(midi): return 440 * 2 ** ((midi - 69) / 12)

def music(bpm=120, duration=10.0, seed=1, key="A", hits=(), style="bed"):
    r = np.random.default_rng(seed); n = int(duration * SR); out = np.zeros((n, 2)); bl = 60 / bpm
    hits = sorted({round(h / (bl / 2)) * (bl / 2) for h in hits})          # snap to half-beat grid
    def muted(t): return any(h - bl / 2 <= t < h for h in hits if h > 0)    # drop-out before each hit
    root = 45 + NOTE[key.upper()] - 9   # A2 = 45
    prog = [0, -4, 3, -2]               # i  VI  III  VII  (minor key, relative semitones)
    # drums
    kt = np.arange(int(0.35 * SR)) / SR
    kick = np.sin(2 * np.pi * np.cumsum(150 * np.exp(-kt * 30) + 45) / SR) * np.exp(-kt * 9)
    ct = np.arange(int(0.25 * SR)) / SR
    clap = fft_filter(r.standard_normal(len(ct)), lo=900, hi=9000) * (np.exp(-ct * 30) + 0.6 * np.exp(-np.maximum(0, ct - 0.012) * 40) * (ct > 0.012))
    ht = np.arange(int(0.05 * SR)) / SR
    hat = fft_filter(r.standard_normal(len(ht)), lo=7000) * np.exp(-ht * 90)
    beats = int(duration / bl) + 1
    for b in range(beats):
        t = b * bl
        if t >= duration: break
        if not muted(t): place(out, kick, t, 0.9 if style != "chill" else 0.6)
        if b % 2 == 1 and not muted(t): place(out, clap, t, 0.35)
        for k in (0, 0.5):
            th = t + k * bl
            if th < duration and not muted(th): place(out, np.stack([hat * (0.8 if k else 0.5), hat * (0.5 if k else 0.8)], 1), th, 0.22 if style != "drive" else 0.3)
    # bass + pad, one chord per bar (4 beats)
    bar = 4 * bl
    for i in range(int(np.ceil(duration / bar))):
        t0 = i * bar; deg = prog[i % 4]; m = root + deg
        seg = int(min(bar, duration - t0) * SR)
        if seg <= 0: break
        tt = np.arange(seg) / SR
        # bass: 8th-note pulses on root, slight saw via 3 harmonics
        bs = np.zeros(seg)
        for k in range(int(bar / (bl / 2))):
            s = int(k * bl / 2 * SR)
            if s >= seg: break
            if muted(t0 + k * bl / 2): continue
            L = min(seg - s, int(bl / 2 * SR * 0.9)); u = np.arange(L) / SR; f = hz(m)
            bs[s:s + L] += (np.sin(2 * np.pi * f * u) + 0.3 * np.sin(4 * np.pi * f * u) + 0.12 * np.sin(6 * np.pi * f * u)) * np.exp(-u * 6) * 0.45
        pad = np.zeros((seg, 2))
        for iv in (12, 15 if deg in (0, 3) else 16, 19):
            for dt, pan in ((-0.08, 0), (0.08, 1)):
                f = hz(m + iv) * 2 ** (dt / 12)
                pad[:, pan] += (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt))
        pad *= (np.minimum(1, tt / 0.3) * np.minimum(1, (tt[-1] - tt + 1e-3) / 0.2))[:, None] * 0.05
        out[int(t0 * SR):int(t0 * SR) + seg] += pad + bs[:, None]
    for h in hits:   # the music lands on every cut
        cr_n = int(1.2 * SR); u = np.arange(cr_n) / SR
        crash = fft_filter(r.standard_normal(cr_n), lo=4000) * np.exp(-u * 3.5) * 0.35
        place(out, np.stack([crash, np.roll(crash, 64)], 1), h)
        place(out, sfx("impact", seed + int(h * 100)), h, 0.6)
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    a1 = sp.add_parser("sfx"); a1.add_argument("--type", required=True); a1.add_argument("--out", required=True); a1.add_argument("--seed", type=int, default=1)
    a2 = sp.add_parser("music"); a2.add_argument("--bpm", type=float, default=120); a2.add_argument("--duration", type=float, default=10); a2.add_argument("--out", required=True)
    a2.add_argument("--seed", type=int, default=1); a2.add_argument("--key", default="A"); a2.add_argument("--hits", default=""); a2.add_argument("--style", default="bed")
    a3 = sp.add_parser("cues"); a3.add_argument("--beats", required=True); a3.add_argument("--out", required=True)
    a4 = sp.add_parser("bed"); a4.add_argument("--beats", required=True); a4.add_argument("--out", required=True); a4.add_argument("--style", default="bed"); a4.add_argument("--key", default="A")
    a = ap.parse_args()
    if a.cmd == "sfx":
        write_wav(a.out, sfx(a.type, a.seed))
    elif a.cmd == "music":
        hits = [float(h) for h in a.hits.split(",") if h.strip()]
        write_wav(a.out, music(a.bpm, a.duration, a.seed, a.key, hits, a.style))
    elif a.cmd == "cues":
        B = json.load(open(a.beats)); n = int(B["duration"] * SR) + SR; tr = np.zeros((n, 2)); cnt = 0
        for b in B["beats"]:
            for i, c in enumerate(b.get("sfx", [])):
                place(tr, sfx(c["type"], B.get("seed", 1) + cnt), float(c["t"]), float(c.get("gain", 0.8))); cnt += 1
        write_wav(a.out, tr[:int(B["duration"] * SR)])
        print(json.dumps({"sfx_track": a.out, "cues": cnt}))
        return
    elif a.cmd == "bed":
        B = json.load(open(a.beats)); hits = [b["t"] for b in B["beats"] if b.get("cut") and b["t"] > 0]
        write_wav(a.out, music(B.get("bpm", 120), B["duration"], B.get("seed", 1), a.key, hits, a.style))
        print(json.dumps({"music": a.out, "bpm": B.get("bpm", 120), "hits": hits})); return
    print(json.dumps({"wrote": a.out}))

if __name__ == "__main__":
    main()
