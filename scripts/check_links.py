#!/usr/bin/env python3
"""check_links.py: verify the single-skill layout and that every relative path in the skill docs resolves.

Checks: exactly one SKILL.md in the repo (video-making/SKILL.md, with name: video-making); every markdown link
target and every backticked path that looks like a pack path (components/..., ../x/..., $PACK/...) in
video-making/**/*.md exists. Placeholders (<dir>, my-video, out/, URLs) are ignored. Exit 1 on any failure.
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
SK = os.path.join(ROOT, "video-making")
fails, checked = [], 0

skills = [os.path.relpath(os.path.join(d, f), ROOT) for d, _, fs in os.walk(ROOT)
          if "/.git" not in d and "node_modules" not in d and "/.venv" not in d for f in fs if f == "SKILL.md"]
if skills != ["video-making/SKILL.md"]: fails.append(f"expected exactly one SKILL.md at video-making/SKILL.md, found {skills}")
head = open(os.path.join(SK, "SKILL.md"), encoding="utf-8").read().split("---")[1]
if not re.search(r"^name:\s*video-making\s*$", head, re.M): fails.append("SKILL.md frontmatter must say name: video-making")

def resolve(md, ref):
    ref = ref.split("#")[0].strip()
    if not ref or "://" in ref or ref.startswith("mailto:") or "<" in ref or "*" in ref: return None
    if ref.startswith("$PACK/"): return os.path.join(ROOT, ref[6:])
    if ref.startswith("/__vsp/pack/"): return os.path.join(ROOT, ref[len("/__vsp/pack/"):])
    if ref.startswith("components/") and os.path.basename(md) == "SKILL.md": return os.path.join(SK, ref)
    if ref.startswith("../") or ref.startswith("./"): return os.path.normpath(os.path.join(os.path.dirname(md), ref))
    if os.path.basename(md) == "SKILL.md" and re.match(r"^(scripts|lib|examples|smoke-test)/", ref): return os.path.join(ROOT, ref)
    return None

for d, _, fs in os.walk(SK):
    for f in fs:
        if not f.endswith(".md"): continue
        md = os.path.join(d, f); text = open(md, encoding="utf-8").read()
        refs = re.findall(r"\]\(([^)\s]+)\)", text)
        for tok in re.findall(r"`([^`\n]+)`", text):
            refs += re.findall(r"(?:\$PACK/|/__vsp/pack/|\.\./|components/)[\w./-]+", tok)
            if re.match(r"^(scripts|lib|examples|smoke-test)/[\w./-]+$", tok): refs.append(tok)
        for ref in refs:
            ref = ref.rstrip(".,;:)")
            p = resolve(md, ref)
            if p is None: continue
            checked += 1
            if not os.path.exists(p): fails.append(f"{os.path.relpath(md, ROOT)}: '{ref}' does not resolve")

for x in fails: print("FAIL:", x)
print(f"link-check: {checked} relative paths checked in video-making/**/*.md, 1 SKILL.md expected, "
      + ("all resolve" if not fails else f"{len(fails)} problem(s)"))
sys.exit(1 if fails else 0)
