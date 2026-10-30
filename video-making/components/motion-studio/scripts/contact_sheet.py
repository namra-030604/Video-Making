#!/usr/bin/env python3
"""Contact sheet: one frame per beat as a labelled grid PNG (for the self-critique loop).

Usage
  python3 contact_sheet.py --project . [--beats beats.json] [--out out/contact_sheet.png]
                           [--every-beat] [--mid] [--cols 4] [--tile 480]
  python3 contact_sheet.py --video out/final.mp4 --beats beats.json        # grab from a rendered mp4 instead

Frames are taken at each beat time (+0.25 beat with --mid so the motion has settled a little),
or at EVERY grid beat (60/bpm) with --every-beat. Writes the grid PNG plus a scorecard template
(out/scorecard_template.json) with the 7 critique axes. Codex can open the PNG and look at it.
"""
import argparse, json, os, subprocess, sys, tempfile, shutil
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.realpath(__file__))


def pack_root():
    """Repo root: $VSP_PACK, else the PACK_ROOT file written by install.sh into copied skills, else ../../../.. from here."""
    if os.environ.get("VSP_PACK"): return os.environ["VSP_PACK"]
    marker = os.path.join(HERE, "..", "..", "..", "PACK_ROOT")
    if os.path.exists(marker): return open(marker).read().strip()
    return os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
AXES = ["readability", "motion_quality", "brand_accuracy", "sound_sync", "composition", "typography", "hook_strength"]

def font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--beats", default=None)
    ap.add_argument("--video", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--tile", type=int, default=480, help="tile width px")
    ap.add_argument("--every-beat", action="store_true")
    ap.add_argument("--mid", action="store_true", help="sample a quarter-beat after each beat")
    a = ap.parse_args()
    proj = os.path.abspath(a.project)
    beats_path = a.beats or os.path.join(proj, "beats.json")
    B = json.load(open(beats_path))
    bpm, dur = B.get("bpm", 120), B["duration"]
    bl = 60.0 / bpm
    if a.every_beat:
        items = []; k = 0
        while k * bl < dur - 1e-6:
            t = k * bl; lab = next((b for b in B["beats"] if abs(b["t"] - t) < 1e-3), None)
            items.append((t, f"beat {k}" + (f" | {lab['id']} {lab.get('section','')}" if lab else ""), lab.get("action", "") if lab else "")); k += 1
    else:
        items = [(b["t"], f"{b['id']} {b.get('section','')}", b.get("action", "")) for b in B["beats"]]
    off = bl * 0.25 if a.mid else 0.0
    times = [min(dur - 1e-3, t + off) for t, _, _ in items]
    tmp = tempfile.mkdtemp(prefix="ms_cs_")
    files = []
    if a.video:
        for i, t in enumerate(times):
            f = os.path.join(tmp, f"{i:03d}.png")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", a.video, "-frames:v", "1", f], check=True)
            files.append(f)
    else:
        # render the stills with the pack's driver (scripts/stills.mjs at the repo root)
        stills = os.path.join(pack_root(), "scripts", "stills.mjs")
        r = subprocess.run(["node", os.path.abspath(stills), "--project", proj, "--times", ",".join(f"{t:.4f}" for t in times)], capture_output=True, text=True)
        sys.stderr.write(r.stderr)
        if r.returncode != 0: sys.exit("stills.mjs failed:\n" + r.stdout[-2000:])
        files = [os.path.join(proj, "out", "stills", f"still_{i + 1:02d}.png") for i in range(len(times))]
    ims = [Image.open(f).convert("RGB") for f in files]
    tw = a.tile; th = int(tw * ims[0].height / ims[0].width); cap = 64
    cols = min(a.cols, len(ims)); rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 12) + 12, rows * (th + cap + 12) + 12), (24, 24, 24))
    d = ImageDraw.Draw(sheet); f1, f2 = font(18), font(13)
    for i, (im, (t, lab, act)) in enumerate(zip(ims, items)):
        x = 12 + (i % cols) * (tw + 12); y = 12 + (i // cols) * (th + cap + 12)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y))
        d.text((x, y + th + 4), f"{times[i]:.2f}s  {lab}", fill=(255, 255, 255), font=f1)
        d.text((x, y + th + 28), act[:int(tw / 7.5)], fill=(180, 180, 180), font=f2)
    out = a.out or os.path.join(proj, "out", "contact_sheet.png")
    os.makedirs(os.path.dirname(out), exist_ok=True); sheet.save(out)
    card = {"round": 1, "sheet": out, "scores": {k: None for k in AXES}, "worst_3_problems": ["", "", ""], "fixes_applied": [],
            "pass_rule": "every axis >= 8, otherwise fix the worst 3 problems and re-render the sheet"}
    with open(os.path.join(os.path.dirname(out), "scorecard_template.json"), "w") as fh: json.dump(card, fh, indent=2)
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"contact_sheet": out, "tiles": len(ims), "times": [round(t, 3) for t in times]}))

if __name__ == "__main__":
    main()
