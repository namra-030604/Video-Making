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
    cfg = json.loads(cfg_path.read_text())
    return root, cfg

def note(root: Path, msg: str):
    """Append one timestamped line to PROGRESS.md (restart-safe log)."""
    with open(root / "PROGRESS.md", "a") as f:
        f.write(f"\n- {time.strftime('%Y-%m-%d %H:%M:%S')} {msg}")

def vget(cfg, path, default=None):
    cur = cfg
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur
