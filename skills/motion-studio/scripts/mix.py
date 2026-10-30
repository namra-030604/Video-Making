#!/usr/bin/env python3
"""mix: music + sfx + voice -> one track, ducked, loudness-normalized to -14 LUFS, optionally muxed onto the video.

Usage
  python3 mix.py --music audio/music.wav --sfx audio/sfx.wav [--voice voice/voiceover.wav] \
                 [--video out/render.mp4] --out out/final.mp4  [--lufs -14] [--tp -1.5]
                 [--music-db -6] [--sfx-db -3] [--voice-db 0] [--no-duck]
  python3 mix.py --measure out/final.mp4         # just print integrated LUFS / true peak / LRA
- Music is side-chain ducked under the voice (about -8 dB while someone talks) so words stay clear.
- Two-pass ffmpeg loudnorm (EBU R128): pass 1 measures, pass 2 applies linear gain to hit the target
  (default -14 LUFS integrated, -1.5 dBTP, the usual streaming target). Then it re-measures and prints the result.
- Output: if --video is given, an mp4 with the video stream copied + AAC 192k; else a 48 kHz WAV.
- Short clips (< ~3 s) read slightly off target because the EBU gate needs 400 ms blocks; that is normal.
"""
import argparse, json, os, re, subprocess, sys, tempfile

def ff(args, capture=True):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats"] + args, capture_output=capture, text=True)
    if r.returncode != 0: sys.exit("ffmpeg failed:\n" + (r.stderr or "")[-1500:])
    return r.stderr

def measure(path):
    err = ff(["-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = err[err.rfind("Summary:"):]
    g = lambda k: float(re.search(k + r":\s+(-?[\d.]+|-inf)", tail).group(1).replace("-inf", "-99"))
    return {"integrated_lufs": g("I"), "lra_lu": g("LRA"), "true_peak_dbfs": g("Peak")}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--music"); ap.add_argument("--sfx"); ap.add_argument("--voice"); ap.add_argument("--video"); ap.add_argument("--out")
    ap.add_argument("--lufs", type=float, default=-14.0); ap.add_argument("--tp", type=float, default=-1.5); ap.add_argument("--lra", type=float, default=11)
    ap.add_argument("--music-db", type=float, default=-6); ap.add_argument("--sfx-db", type=float, default=-3); ap.add_argument("--voice-db", type=float, default=0)
    ap.add_argument("--no-duck", action="store_true"); ap.add_argument("--measure")
    a = ap.parse_args()
    if a.measure:
        print(json.dumps(measure(a.measure), indent=1)); return
    ins, labels = [], []
    for name, path, db in (("m", a.music, a.music_db), ("s", a.sfx, a.sfx_db), ("v", a.voice, a.voice_db)):
        if path: ins.append((name, path, db))
    if not ins or not a.out: ap.error("need --out and at least one of --music/--sfx/--voice")
    args = []
    for _, p, _ in ins: args += ["-i", p]
    fc = []
    for i, (n, _, db) in enumerate(ins):
        fc.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,volume={db}dB[{n}]")
    names = [n for n, _, _ in ins]
    if "v" in names and "m" in names and not a.no_duck:
        fc.append("[v]asplit=2[v1][vk]")
        fc.append("[m][vk]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350:makeup=1[md]")
        parts = ["[md]"] + (["[s]"] if "s" in names else []) + ["[v1]"]
    else:
        parts = [f"[{n}]" for n in names]
    fc.append("".join(parts) + f"amix=inputs={len(parts)}:duration=longest:normalize=0[pre]")
    tmp = tempfile.mkdtemp(prefix="ms_mix_"); pre = os.path.join(tmp, "pre.wav")
    ff(["-y"] + args + ["-filter_complex", ";".join(fc), "-map", "[pre]", "-ar", "48000", pre])
    # pass 1: measure
    def pass1(path):
        err = ff(["-i", path, "-af", f"loudnorm=I={a.lufs}:TP={a.tp}:LRA={a.lra}:print_format=json", "-f", "null", "-"])
        return json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    js = pass1(pre)
    gain = a.lufs - float(js["input_i"])
    if float(js["input_tp"]) + gain > a.tp - 0.5:
        # peaks would clip after the gain: soft-limit the transients first so loudnorm can stay linear (no pumping)
        lim = max(0.0625, 10 ** ((a.tp - 1.0 - gain) / 20))
        limited = os.path.join(tmp, "lim.wav")
        ff(["-y", "-i", pre, "-af", f"alimiter=limit={lim:.4f}:attack=2:release=60:level=disabled", "-ar", "48000", limited])
        os.replace(limited, pre); js = pass1(pre)
    lra = min(50, max(a.lra, float(js["input_lra"]) + 1))   # loudnorm falls back to 'dynamic' if LRA target < measured LRA
    ln = (f"loudnorm=I={a.lufs}:TP={a.tp}:LRA={lra}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    norm = os.path.join(tmp, "norm.wav")
    ff(["-y", "-i", pre, "-af", ln + ",aresample=48000", "-ar", "48000", norm])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    if a.video:
        ff(["-y", "-i", a.video, "-i", norm, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", a.out])
    else:
        ff(["-y", "-i", norm, "-c:a", "pcm_s16le", a.out])
    m = measure(a.out)
    m.update({"out": a.out, "target_lufs": a.lufs, "pre_norm_lufs": float(js["input_i"])})
    print(json.dumps(m, indent=1))
    for f in (pre, norm): os.remove(f)
    os.rmdir(tmp)

if __name__ == "__main__":
    main()
