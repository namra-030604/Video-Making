#!/usr/bin/env python3
"""qc_final.py - measurable delivery gates for a finished MP4. Prints a PASS/FAIL table, exits 1 on any FAIL.

Checks: resolution + fps match project.json, duration matches the voice timeline (+-0.15 s), audio/video
streams end within 0.1 s, loudness -14 +-0.5 LUFS integrated and true peak <= -1.5 dBTP (configurable),
no black stretch >= 0.5 s (ffmpeg blackdetect), no frozen stretch >= freeze_s (default 0.75 s, freezedetect),
no near-blank frames sampled at 4 fps, file size under max_mb, narration pace within the wpm window.
Also writes out/qc/contact_sheet.png (6 frames) and out/qc/qc_final.json.

Usage: python scripts/qc_final.py --project DIR [--video out/NAME.mp4]
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from vsp_common import load_project, note, vget

def sh(*a): return subprocess.run(a, capture_output=True, text=True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--project", default="."); ap.add_argument("--video")
    a = ap.parse_args()
    root, cfg = load_project(a.project)
    video = Path(a.video) if a.video else root / (cfg.get("output") or f"out/{cfg.get('name', 'video')}.mp4")
    if not video.is_absolute(): video = (Path.cwd() / video) if a.video else video
    if not video.exists(): sys.exit(f"video not found: {video}")
    W, H, fps = cfg.get("width", 1080), cfg.get("height", 1920), cfg.get("fps", 30)
    meta_p = root / "audio/voice_meta.json"; meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    want_dur = cfg.get("duration") or meta.get("duration")
    q = cfg.get("qc", {})
    lufs, tp_max = float(vget(cfg, "audio.lufs", -14)), float(vget(cfg, "audio.true_peak", -1.5))
    freeze_s, max_mb = float(q.get("freeze_s", 0.75)), float(q.get("max_mb", 200))
    wpm_lo, wpm_hi = q.get("wpm_range", [150, 172])
    rows = []
    def gate(name, ok, value, need): rows.append({"gate": name, "result": "PASS" if ok else "FAIL", "value": value, "need": need})
    def skip(name, why): rows.append({"gate": name, "result": "SKIP", "value": why, "need": ""})

    info = json.loads(sh("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)).stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video"); au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    gate("resolution", (v["width"], v["height"]) == (W, H), f"{v['width']}x{v['height']}", f"{W}x{H}")
    gate("fps", v["r_frame_rate"] == f"{fps}/1", v["r_frame_rate"], f"{fps}/1")
    gate("pixel format", v.get("pix_fmt") == "yuv420p", v.get("pix_fmt"), "yuv420p")
    dur = float(info["format"]["duration"])
    if want_dur: gate("duration", abs(dur - want_dur) <= 0.15, f"{dur:.3f}s", f"{want_dur:.3f}s +-0.15")
    else: skip("duration", "no target")
    if au:
        vd, ad = float(v.get("duration", dur)), float(au.get("duration", dur))
        gate("a/v sync (stream ends)", abs(vd - ad) <= 0.1, f"{abs(vd - ad):.3f}s", "<= 0.1s")
        r = sh("ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-af", "loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json", "-vn", "-f", "null", "-")
        m = json.loads(re.search(r'\{\s*"input_i".*?\}', r.stderr, re.S).group())
        I, TP = float(m["input_i"]), float(m["input_tp"])
        gate("loudness", abs(I - lufs) <= 0.5, f"{I:.2f} LUFS", f"{lufs} +-0.5")
        gate("true peak", TP <= tp_max, f"{TP:.2f} dBTP", f"<= {tp_max}")
    else:
        gate("audio stream", False, "missing", "AAC audio")
    r = sh("ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf", "blackdetect=d=0.5:pix_th=0.10", "-an", "-f", "null", "-")
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)
    gate("no black >= 0.5s", not blacks, f"{len(blacks)} stretch(es)", "0")
    r = sh("ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf", f"freezedetect=n=0.001:d={freeze_s}", "-an", "-f", "null", "-")
    freezes = re.findall(r"freeze_start: ([\d.]+)", r.stderr)
    gate(f"no static >= {freeze_s}s", not freezes, f"{len(freezes)} stretch(es)" + (f" at {freezes[:3]}" if freezes else ""), "0")
    r = sh("ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf", "fps=4,signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-an", "-f", "null", "-")
    yavg = [float(x) for x in re.findall(r"YAVG=([\d.]+)", r.stderr)]
    dark = [i / 4 for i, y in enumerate(yavg) if y < 12]
    gate("no near-blank samples (4 fps)", not dark, f"{len(dark)}/{len(yavg)} dark", "0")
    mb = video.stat().st_size / 1e6
    gate("file size", mb <= max_mb, f"{mb:.2f} MB", f"<= {max_mb} MB")
    if meta.get("wpm_overall"):
        wpm = meta["wpm_overall"]
        if meta.get("duration", 99) < 15: rows.append({"gate": "pace (wpm)", "result": "INFO", "value": f"{wpm:.0f} wpm", "need": f"{wpm_lo}-{wpm_hi} (not enforced under 15 s)"})
        else: gate("pace (wpm)", wpm_lo <= wpm <= wpm_hi, f"{wpm:.0f} wpm", f"{wpm_lo}-{wpm_hi}")
    al = root / "align/words.json"
    if al.exists():
        frac = json.loads(al.read_text()).get("matched_fraction", 0); gate("words aligned", frac >= 0.97, f"{frac:.1%}", ">= 97%")
    sq = root / "out/subtitle_qc.json"
    if sq.exists(): gate("subtitle QC", json.loads(sq.read_text()).get("pass") is True, "see out/subtitle_qc.json", "pass")
    else: skip("subtitle QC", "run subtitle_qc.mjs")
    qd = root / "out/qc"; qd.mkdir(parents=True, exist_ok=True)
    sh("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video), "-vf", f"fps=6/{max(dur, 0.1):.3f},scale=-2:360,tile=6x1:padding=6:margin=6", "-frames:v", "1", str(qd / "contact_sheet.png"))
    ok = all(r["result"] != "FAIL" for r in rows)
    (qd / "qc_final.json").write_text(json.dumps({"video": video.name, "pass": ok, "gates": rows}, indent=2) + "\n")
    w = max(len(r["gate"]) for r in rows)
    print(f"{'GATE'.ljust(w)}  RESULT  VALUE  (NEED)")
    for r in rows: print(f"{r['gate'].ljust(w)}  {r['result']:<6}  {r['value']}  ({r['need']})")
    print("OVERALL:", "PASS" if ok else "FAIL")
    note(root, f"qc_final: {'PASS' if ok else 'FAIL'} ({video.name}, {mb:.2f} MB)")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
