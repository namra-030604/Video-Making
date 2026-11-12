# Agent install guide

Use the OS-specific one-line clone and install command in [README.md](README.md). The native command after cloning is `python3 vsp.py install` on Linux/macOS or `py -3 vsp.py install` on Windows. The POSIX `install.sh` and Windows `install.ps1` wrappers call the same Python CLI. `install --check`, `check`, and `install --dry-run` list present/missing system tools and exact install commands without making changes. `--install-system` runs package manager commands only without a password prompt; `--apt` is an alias. If no supported bootstrap Python or pip is available, install uv with `brew install uv` (macOS), `winget install --id astral-sh.uv -e` (Windows), or `python3 -m pip install --user uv==0.13.7` (Linux), then rerun.

The installer creates `.venv` with uv-managed Python 3.13 and writes `.vsp-state/python` for compatibility. It uses `requirements.lock.txt` for full video and `requirements-voice.lock.txt` for voice-only mode and verifies SHA256 for all model/font/Chrome downloads. The cache is `VSP_CACHE` or `${XDG_CACHE_HOME:-~/.cache}/video-skill-pack` on every OS. Chrome-for-Testing is pinned per platform. It links `video-making` into existing Codex/Claude skill directories; on Windows it copies by default. Use `python vsp.py link-skills --skills-dir DIR` for another agent, `--copy` to copy, or `--relink` to repoint a previous pack link.

## Supported systems

Linux x86_64, **macOS 14 or newer**, and Windows 10/11 x64 are supported. Full video on macOS requires Apple Silicon. Intel Macs, including x86_64 Python under Rosetta, automatically use voice-only mode with onnxruntime 1.23.2; `--voice-only` or `VSP_VOICE_ONLY=1` forces that tier anywhere. Full video requires Node 18+ and ffmpeg/ffprobe with libx264; voice-only needs ffmpeg for mixing. Python 3.8+ or uv starts the installer; uv creates runtime Python 3.13 (3.12-3.13 supported).

## Verify and work

```text
python3 vsp.py verify
python3 vsp.py smoke
python3 vsp.py new my-video
python3 vsp.py build my-video
```
On Windows PowerShell, replace `python3` with `py -3`.

`verify` exercises the installed tier; full video checks packages, ffmpeg, ffprobe, models, Chrome rendering, routing and links. `smoke` runs the seven stages with restart markers under `smoke-test/out/`, then requires `qc_final.json` to say `pass: true`. `smoke --clean` restarts. `build <dir> --force` rebuilds stages. `new <dir> --motion --vertical` scaffolds a vertical motion-studio project. Use `python vsp.py uninstall-notes` to list installed paths; it removes nothing.

Set `VSP_FFMPEG`, `VSP_FFPROBE`, `VSP_NODE`, `VSP_BLENDER` or `CHROME` for nonstandard executable locations. The finder also checks PATH and common Homebrew, WinGet, Chocolatey, ffmpeg and Blender directories. `--with-blender` checks the optional Blender executable. `--with-maps`, `--with-puppeteer`, `--with-hyperframes` and `--with-remotion` install optional npm packages.

MMS_FA model weights are **CC-BY-NC 4.0 (non-commercial)**. Do not use that model for commercial captions. The first install downloads about 1.26 GB for MMS_FA unless `--skip-aligner` is selected. Run one heavy stage at a time and report unverified outputs honestly.

## Voice-only commands

On Intel Macs, `install` selects voice-only automatically and does not download Torch, MMS_FA, or Chrome. On any OS, force the tier with `python3 vsp.py install --voice-only` (Windows: `py -3 vsp.py install --voice-only`). Run `python3 vsp.py new my-video`, edit `project.json`, then `python3 vsp.py voice my-video` and `python3 vsp.py audio my-video`. `scripts/make_voice.py` and the audio mix scripts remain available. `build`, `smoke`, direct stills/render and subtitle QC exit with one friendly message because the pinned stack does not support Intel Mac video rendering. `verify` checks the voice tier without requiring Node, Torch or Chrome.
