#!/usr/bin/env python3
"""beatsheet: check (and optionally snap) beats.json to the BPM grid BEFORE any drawing code is written.

Usage  python3 beatsheet.py beats.json [--snap] [--grid 1|0.5|0.25]  [--new 10 --bpm 120 > beats.json]
Checks
  - every beat has id, t, section, action; times ascending; inside duration
  - cuts ("cut": true) land on the grid (default whole beats, 60/bpm s) within 1 frame -> music lands on the cut
  - every sfx cue sits inside its beat and has a known type (click whoosh pop impact riser tick swoosh_down)
  - first beat at 0.0 is a Hook and something happens in the first 1-2 s (hook rule)
  - warns if a gap between beats is > 2 s (dead air)
Prints a readable table. --snap rewrites times to the nearest grid point. --new N makes an empty N-second template.
"""
import argparse, json, sys
SFX = {"click", "whoosh", "pop", "impact", "riser", "tick", "swoosh_down"}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?"); ap.add_argument("--snap", action="store_true"); ap.add_argument("--grid", type=float, default=1.0)
    ap.add_argument("--new", type=float); ap.add_argument("--bpm", type=float, default=120)
    a = ap.parse_args()
    if a.new:
        bl = 60 / a.bpm; beats = []
        sections = ["Hook", "Hook", "Feature 1", "Feature 1", "Feature 2", "Feature 2", "Payoff", "Outro"]
        k, i = 0, 0
        while k * bl * 2 < a.new - 1e-6:
            sec = sections[min(i, len(sections) - 1)]
            beats.append({"id": f"{i // 2 + 1}.{i % 2 + 1}", "t": round(k * bl * 2, 3), "section": sec, "action": "TODO: what the cursor/UI/type does", "cut": i % 2 == 0, "sfx": []})
            k += 1; i += 1
        print(json.dumps({"title": "TODO", "bpm": a.bpm, "fps": 60, "size": [1920, 1080], "duration": a.new, "seed": 1, "beats": beats, "voice": None}, indent=2)); return
    B = json.load(open(a.path)); bl = 60 / B.get("bpm", 120); g = bl * a.grid; fps = B.get("fps", 60); dur = B["duration"]
    errs, warns = [], []
    prev = -1
    for b in B["beats"]:
        for k in ("id", "t", "section", "action"):
            if k not in b: errs.append(f"beat {b.get('id','?')} missing '{k}'")
        t = b.get("t", 0)
        if a.snap: b["t"] = t = round(round(t / g) * g, 4)
        if t <= prev: errs.append(f"beat {b['id']} time {t} not after previous {prev}")
        if t > dur: errs.append(f"beat {b['id']} at {t}s is past duration {dur}s")
        if prev >= 0 and t - prev > 2.0: warns.append(f"{t - prev:.1f}s gap before {b['id']} (dead air? add a move)")
        off = abs(t / g - round(t / g)) * g
        if b.get("cut") and off > 1 / fps: errs.append(f"cut {b['id']} at {t}s is {off:.3f}s off the {g:.3f}s grid")
        for c in b.get("sfx", []):
            if c.get("type") not in SFX: errs.append(f"beat {b['id']} sfx type '{c.get('type')}' unknown")
            if c.get("t", t) < t - 1e-6: warns.append(f"beat {b['id']} sfx at {c.get('t')}s is before its beat")
        prev = t
    if not B["beats"] or B["beats"][0]["t"] != 0 or "hook" not in B["beats"][0].get("section", "").lower():
        errs.append("first beat must be at 0.0s and be the Hook (strong first 1-2 s)")
    print(f"{'id':6} {'time':>7} {'beat#':>6}  {'section':12} {'cut':3}  action")
    for b in B["beats"]:
        print(f"{b['id']:6} {b['t']:7.3f} {b['t'] / bl:6.2f}  {b.get('section',''):12} {'Y' if b.get('cut') else ' ':3}  {b.get('action','')}"
              + (f"   sfx: {', '.join(c['type'] + '@' + str(c['t']) for c in b.get('sfx', []))}" if b.get("sfx") else ""))
    for w in warns: print("WARN ", w)
    for e in errs: print("ERROR", e)
    if a.snap: json.dump(B, open(a.path, "w"), indent=2); print("snapped and saved")
    print("OK" if not errs else "FIX THE ERRORS ABOVE"); sys.exit(1 if errs else 0)

if __name__ == "__main__":
    main()
