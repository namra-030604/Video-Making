#!/usr/bin/env python3
"""framediff: prove the video actually moves, and catch full-screen flashing.

Usage  python3 framediff.py out/final.mp4 [--fps 10] [--threshold 8] [--static-sec 0.75] [--json out/framediff.json]

- Decodes the video at --fps (default 10) in grayscale at 320 px wide.
- motion % = share of pixels that changed by MORE than --threshold gray levels (default 8) vs the previous
  sample. (A naive "any change" count is inflated by grain/noise, so we use a threshold.)
- STATIC: any stretch longer than --static-sec where motion < 0.5 %  (dead air: add drift, parallax, type motion).
- FLASH: a jump where mean brightness changes by > 25 % of full scale AND > 60 % of the frame changes by > 40 levels,
  i.e. a full-screen flash. Not allowed (accessibility + "no full-screen flashing" rule).
Exit code 0 = pass, 3 = problems found. Prints a JSON report.
"""
import argparse, json, subprocess, sys
import numpy as np

def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                        "-of", "json", path], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout); s = j["streams"][0]
    return s["width"], s["height"], float(j["format"]["duration"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--fps", type=float, default=10); ap.add_argument("--threshold", type=int, default=8)
    ap.add_argument("--static-sec", type=float, default=0.75); ap.add_argument("--json", default=None)
    a = ap.parse_args()
    w, h, dur = probe(a.video)
    ow = 320; oh = int(round(h * ow / w / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a.video, "-vf", f"fps={a.fps},scale={ow}:{oh}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, oh, ow).astype(np.int16)
    motion, flashes, rows = [], [], []
    for i in range(1, len(fr)):
        d = np.abs(fr[i] - fr[i - 1])
        m = float((d > a.threshold).mean() * 100)
        dmean = abs(float(fr[i].mean() - fr[i - 1].mean())) / 255 * 100
        big = float((d > 40).mean() * 100)
        t = i / a.fps
        motion.append(m); rows.append({"t": round(t, 2), "motion_pct": round(m, 2), "mean_luma_jump_pct": round(dmean, 1)})
        if dmean > 25 and big > 60: flashes.append(round(t, 2))
    statics, start = [], None
    for i, m in enumerate(motion + [100]):
        t = (i + 1) / a.fps
        if m < 0.5 and start is None: start = t - 1 / a.fps
        if m >= 0.5 and start is not None:
            if t - 1 / a.fps - start >= a.static_sec: statics.append([round(start, 2), round(t - 1 / a.fps, 2)])
            start = None
    rep = {"video": a.video, "size": [w, h], "duration": round(dur, 3), "samples": len(fr), "threshold_gray": a.threshold,
           "mean_motion_pct": round(float(np.mean(motion)), 2) if motion else 0, "min_motion_pct": round(float(np.min(motion)), 2) if motion else 0,
           "static_stretches_sec": statics, "full_screen_flashes_at": flashes,
           "verdict": "PASS" if not statics and not flashes else "FIX", "per_sample": rows}
    if a.json:
        with open(a.json, "w") as fh: json.dump(rep, fh, indent=2)
    short = {k: v for k, v in rep.items() if k != "per_sample"}
    print(json.dumps(short, indent=2))
    sys.exit(0 if rep["verdict"] == "PASS" else 3)

if __name__ == "__main__":
    main()
