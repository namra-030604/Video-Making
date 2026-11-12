#!/usr/bin/env python3
"""Check the single-skill layout and relative links in the skill docs."""
import os
import re
import sys
from pathlib import Path, PurePath

ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / 'video-making'
EXPECTED_SKILL = ('video-making', 'SKILL.md')
SKIP_DIRS = {'.git', '.venv', 'node_modules', '.vsp-cache', '.vsp-state', '__pycache__'}


def is_expected_skill_path(path: PurePath):
    """Compare components so Windows separators never affect the result."""
    return path.parts == EXPECTED_SKILL


def skill_files(root: Path):
    found = []
    for directory, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for name in files:
            if name == 'SKILL.md':
                found.append(Path(directory) / name)
    return found


def resolve(md: Path, ref: str, root: Path = ROOT, skill: Path = SK):
    ref = ref.split('#')[0].strip()
    if not ref or '://' in ref or ref.startswith('mailto:') or '<' in ref or '*' in ref:
        return None
    if ref.startswith('$PACK/'):
        return root / ref[6:]
    if ref.startswith('/__vsp/pack/'):
        return root / ref[len('/__vsp/pack/'):]
    if ref.startswith('components/') and md.name == 'SKILL.md':
        return skill / ref
    if ref.startswith('../') or ref.startswith('./'):
        return md.parent / ref
    if md.name == 'SKILL.md' and re.match(r'^(scripts|lib|examples|smoke-test)/', ref):
        return root / ref
    return None


def check(root: Path = ROOT):
    skill = root / 'video-making'
    fails, checked = [], 0
    skills = [p.relative_to(root) for p in skill_files(root)]
    if len(skills) != 1 or not is_expected_skill_path(skills[0]):
        fails.append(f'expected exactly one SKILL.md at video-making/SKILL.md, found {[p.as_posix() for p in skills]}')
    head = (skill / 'SKILL.md').read_text(encoding='utf-8').split('---')[1]
    if not re.search(r'^name:\s*video-making\s*$', head, re.M):
        fails.append('SKILL.md frontmatter must say name: video-making')
    for md in skill.rglob('*.md'):
        content = md.read_text(encoding='utf-8')
        refs = re.findall(r'\]\(([^)\s]+)\)', content)
        for tok in re.findall(r'`([^`\n]+)`', content):
            refs += re.findall(r'(?:\$PACK/|/__vsp/pack/|\.\./|components/)[\w./-]+', tok)
            if re.match(r'^(scripts|lib|examples|smoke-test)/[\w./-]+$', tok):
                refs.append(tok)
        for ref in refs:
            ref = ref.rstrip('.,;:)')
            path = resolve(md, ref, root, skill)
            if path is None:
                continue
            checked += 1
            if ref == '$PACK/.vsp-state/python':
                continue
            if not path.exists():
                fails.append(f"{md.relative_to(root).as_posix()}: '{ref}' does not resolve")
    return fails, checked


def main():
    fails, checked = check()
    for problem in fails:
        print('FAIL:', problem)
    print(f'link-check: {checked} relative paths checked in video-making/**/*.md, 1 SKILL.md expected, '
          + ('all resolve' if not fails else f'{len(fails)} problem(s)'))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
