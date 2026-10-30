#!/usr/bin/env python3
"""router_test.py: deterministic KEYWORD check of the router table in video-making/SKILL.md.

This is NOT an LLM test. It proves that (1) every path in the routing table exists, (2) for each sample prompt in
tests/router_cases.json the table contains a matching keyword that routes to the expected component, using the
rule written in SKILL.md: most whole-word keyword matches wins, ties go to the earlier row, no match -> the
default row. Usage: python3 scripts/router_test.py [--quiet]   (exit 1 on any failure)
"""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
SKILL_DIR = os.path.join(ROOT, "video-making")

def table():
    text = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
    sec = text.split("## Routing table", 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0] in ("Intent", "---") or set(cells[0]) <= set("-"): continue
        path = re.search(r"`([^`]+)`", cells[2]).group(1)
        rows.append({"intent": cells[0].replace("*", ""), "keywords": [k.strip().lower() for k in cells[1].split(",") if k.strip()],
                     "path": path, "default": "(default)" in cells[0]})
    return rows

def route(prompt, rows):
    p = prompt.lower(); best, hits = None, []
    for r in rows:
        m = [k for k in r["keywords"] if re.search(r"(?<![\w-])" + re.escape(k) + r"(?![\w-])", p)]
        if len(m) > len(hits): best, hits = r, m
    if best is None: best = next(r for r in rows if r["default"])
    return best, hits

def main():
    rows = table(); fails = 0
    defaults = [r for r in rows if r["default"]]
    if len(defaults) != 1: print("FAIL: routing table needs exactly one (default) row"); fails += 1
    for r in rows:
        if not os.path.isfile(os.path.join(SKILL_DIR, r["path"])): print("FAIL: missing component", r["path"]); fails += 1
    cases = json.load(open(os.path.join(ROOT, "tests", "router_cases.json")))
    print(f"{'prompt':<46} {'routed to':<56} {'matched keywords':<34} result")
    for c in cases:
        r, hits = route(c["prompt"], rows)
        ok = r["path"] == c["expect"] and os.path.isfile(os.path.join(SKILL_DIR, c["expect"]))
        fails += not ok
        print(f"{c['prompt'][:45]:<46} {r['path']:<56} {(', '.join(hits) or '(none: default)')[:33]:<34} {'PASS' if ok else 'FAIL (expected ' + c['expect'] + ')'}")
    print(f"\nrouter keyword test: {len(cases) - min(fails, len(cases))}/{len(cases)} cases, {len(rows)} table rows, " + ("all PASS" if not fails else f"{fails} FAIL"))
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
