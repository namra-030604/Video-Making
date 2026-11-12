"""Shared helpers for the video skill pack Python scripts (paths, project.json, PROGRESS.md)."""
import json, os, sys, time
from pathlib import Path

def cache_dir() -> Path:
    base = os.environ.get("VSP_CACHE") or os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "video-skill-pack")
    return Path(base)

def models_dir() -> Path:
    return cache_dir() / "models"

def load_project(project_dir: str):
    root = Path(project_dir).resolve()
    cfg_path = root / "project.json"
    if not cfg_path.exists():
        sys.exit(f"project.json not found in {root}")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    return root, cfg

def note(root: Path, msg: str):
    """Append one timestamped line to PROGRESS.md (restart-safe log)."""
    with open(root / "PROGRESS.md", "a", encoding="utf-8") as f:
        f.write(f"\n- {time.strftime('%Y-%m-%d %H:%M:%S')} {msg}")

def vget(cfg, path, default=None):
    cur = cfg
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def tool_path(name: str, required: bool = True, system=None, environ=None, which=None, extra_dirs=None):
    """Find an executable from override, PATH, then common OS install directories.

    extra_dirs replaces the OS directories when supplied, so discovery can be
    tested without depending on tools installed on the test machine.
    """
    import glob
    import shutil
    system = system or sys.platform
    env = environ if environ is not None else os.environ
    which = which or shutil.which
    key = {'ffmpeg': 'VSP_FFMPEG', 'ffprobe': 'VSP_FFPROBE', 'node': 'VSP_NODE', 'blender': 'VSP_BLENDER'}.get(name)
    if key and env.get(key):
        p = Path(env[key])
        if p.is_file(): return str(p)
        if required: raise FileNotFoundError(f'{key} points to a missing file: {p}')
        return None
    found = which(name) or (which(name + '.exe') if system == 'win32' else None)
    if found: return found
    if extra_dirs is not None:
        dirs = extra_dirs
    elif system == 'darwin':
        dirs = ['/opt/homebrew/bin', '/usr/local/bin']
        if name == 'blender': dirs += ['/Applications/Blender.app/Contents/MacOS']
    elif system == 'win32':
        dirs = [str(Path(env.get('LOCALAPPDATA', '')) / 'Microsoft/WinGet/Links'),
                str(Path(env.get('ProgramData', 'C:/ProgramData')) / 'chocolatey/bin'), 'C:/ffmpeg/bin']
        if name == 'blender':
            dirs += [str(Path(p)) for p in glob.glob(str(Path(env.get('ProgramFiles', 'C:/Program Files')) / 'Blender Foundation/Blender*/'))]
    else:
        dirs = []
    exe = name + ('.exe' if system == 'win32' else '')
    for d in dirs:
        p = Path(d) / exe
        if p.is_file(): return str(p)
    if not required or name == 'blender': return None
    cmd = 'brew install ffmpeg node' if system == 'darwin' else ('winget install -e --id Gyan.FFmpeg; winget install -e --id OpenJS.NodeJS.LTS' if system == 'win32' else 'sudo apt-get install -y ffmpeg nodejs npm')
    raise FileNotFoundError(f'{name} missing. Install with: {cmd}')


def font_path(cache=None, system=None, environ=None):
    """Prefer the pinned pack font, then platform fonts; return None for Pillow's default."""
    import glob
    env = environ if environ is not None else os.environ
    system = system or sys.platform
    cache = Path(cache) if cache is not None else cache_dir()
    candidate = cache / 'fonts/Inter.ttf'
    if candidate.is_file(): return candidate
    if system == 'darwin': roots = ['/System/Library/Fonts', '/Library/Fonts', str(Path.home() / 'Library/Fonts')]
    elif system == 'win32': roots = [str(Path(env.get('WINDIR', 'C:/Windows')) / 'Fonts')]
    else: roots = ['/usr/share/fonts', str(Path.home() / '.local/share/fonts')]
    for root in roots:
        for pattern in ('*Inter*.ttf', '*DejaVuSans*.ttf', '*Arial*.ttf', '*.ttf'):
            matches = glob.glob(str(Path(root) / '**' / pattern), recursive=True)
            if matches: return Path(matches[0])
    return None
