# Video-Making: a video skill pack for AI coding agents

One installable agent skill (`video-making`), scripts and a tested pipeline that let an AI agent (Codex,
Claude Code, or any agent that reads `SKILL.md` files) make narrated, captioned, music-backed videos **entirely from code, with free local tools**:
Kokoro text-to-speech, word-exact karaoke subtitles, canvas animation captured one frame at a time by headless
Chrome, ffmpeg mixing at -14 LUFS, and automatic quality checks.

## Quick start

Linux (x86_64; Python 3.8+ bootstrap, Node 18+, ffmpeg with libx264):
```sh
git clone https://github.com/namra-030604/Video-Making && cd Video-Making && sh install.sh --install-system
```
macOS 14+ (Apple Silicon full video; Intel Mac automatically gets voice-only; Python 3.8+ or uv bootstrap):
```sh
git clone https://github.com/namra-030604/Video-Making && cd Video-Making && sh install.sh --install-system
```
Windows 10/11 x64 (PowerShell; Python 3.8+ bootstrap, Node and ffmpeg):
```powershell
git clone https://github.com/namra-030604/Video-Making; cd Video-Making; powershell -ExecutionPolicy Bypass -File .\install.ps1 --install-system
```
The installer uses uv to create `.venv` with Python 3.13, downloads pinned models, fonts and Chrome, then links the skill. Install uv with `brew install uv` on macOS or `winget install --id astral-sh.uv -e` on Windows if the automatic pinned pip bootstrap is unavailable. Linux can use `python3 -m pip install --user uv==0.13.7`. Run `python3 vsp.py install --check` (or `py -3 vsp.py install --check` on Windows) first to see missing system tools and exact commands. `--install-system` (`--apt`) runs those commands only when no password prompt is needed.

**For AI agents:** Clone the repo and run the one install command above for the operator's OS. Then run `python3 vsp.py verify` and `python3 vsp.py smoke` on Linux/macOS, or `py -3 vsp.py verify` and `py -3 vsp.py smoke` on Windows; proceed with a project only when verify reports all required components PASS and smoke reports PASS. Create a project with `python3 vsp.py new my-video` and build it with `python3 vsp.py build my-video` on POSIX; use `py -3` in place of `python3` on Windows. The shell wrappers still work on POSIX; Windows uses `vsp.py` directly. See [AGENT_INSTALL.md](AGENT_INSTALL.md).

## One skill: router -> master video -> components
```
video-making/
  SKILL.md                     the ONLY skill entry point: a router (keywords -> component -> what to run)
  components/
    master-video/MASTER.md     full end-to-end orchestration (default route for "make a video")
    script-writing/  voice-and-audio/  subtitles-karaoke/  vertical-9-16-framing/  short-form-editing/
    qc-and-render/  lessons-from-failures/  video-production-standard/      (each a COMPONENT.md)
    motion-studio/   COMPONENT.md + templates/ scripts/ references/        (music-led motion pieces)
    motion-graphics/ COMPONENT.md + fx.js + guides/ (18 effect guides) + gallery/ + test/
```
The router reads the request and sends the agent to one component: script/text, voice/music/SFX/loudness,
motion graphics (or the maps guide), music-led promos, captions/karaoke, 9:16 framing, short-form editing,
rendering/QC/resume, lessons, the production standard, or (default, for a whole video) the master component.
`python3 scripts/router_test.py` checks the routing table against `tests/router_cases.json`: it is a
deterministic **keyword** check, not an LLM test.

## What you get
| Folder | Contents |
|---|---|
| `video-making/` | the single skill (router `SKILL.md`, master component, 10 sub-components, 18 motion guides) |
| `scripts/` | the pipeline: `make_voice.py`, `align_words.py`, `make_audio.py`, `stills.mjs`, `render.mjs`, `subtitle_qc.mjs`, `qc_final.py`, `framediff.py`, `build.sh`, `new_project.sh`; checks: `router_test.py`, `check_links.py` |
| `tests/router_cases.json` | sample prompts and the component each must route to |
| `lib/browser.mjs` | a small dependency-free Chrome DevTools driver (no npm packages needed) |
| `examples/hello-world/` | a complete 540x960 narrated scene to copy |
| `smoke-test/run.sh` | end-to-end test of the whole pipeline |
| `vsp.py`, `install.sh`, `install.ps1` | portable installer, verification and pipeline; POSIX and PowerShell wrappers |
| `requirements.lock.txt`, `requirements-voice.lock.txt` | universal full-video and voice-only Python locks |

## Requirements

- Linux x86_64, **macOS 14 or newer** (Apple Silicon for full video; Intel Mac for voice-only), or Windows 10/11 x64. Intel Mac detection includes x86_64 processes under Rosetta. The voice-only tier uses onnxruntime 1.23.2 and skips Torch, MMS_FA, Chrome, and video rendering. Force that tier on any OS with `--voice-only` or `VSP_VOICE_ONLY=1`.
- Python 3.8+ or uv for the bootstrap; uv creates the runtime Python 3.13 venv. Python 3.12-3.13 is the supported runtime window. Without uv, install Python 3.13 or 3.12 (`py -3.13`/`py -3.12` on Windows, `python3.13`/`python3.12` elsewhere), then install uv. The default installer uses uv because it manages the interpreter.
- Full video needs Node 18+ and ffmpeg/ffprobe with libx264. Voice-only needs ffmpeg for audio mixing. `install --check` reports missing tools. `VSP_FFMPEG`, `VSP_FFPROBE`, `VSP_NODE`, `VSP_BLENDER` and `CHROME` override discovery. Chrome is otherwise downloaded as a pinned build.
- About 4 GB free disk and 2 GB free RAM. No GPU, API key or paid account. Set `VSP_CACHE` to move the cache; otherwise it is `${XDG_CACHE_HOME:-~/.cache}/video-skill-pack` on every OS.

### Download sizes (first install, cached afterwards)
| Item | Size |
|---|---|
| Full-video Python venv (CPU PyTorch, onnxruntime, kokoro-onnx...) | ~1.1 GB on disk; voice-only is smaller |
| Kokoro v1.0 int8 model + voices | ~120 MB |
| MMS_FA alignment model (skipped in voice-only or with `--skip-aligner`) | ~1.26 GB |
| chrome-headless-shell 156.0.8078.47 (skipped with `--no-chrome` or voice-only) | ~126 MB zip, ~270 MB unpacked |
| Inter + Caveat fonts | ~1.3 MB |

### Intel Mac and forced voice-only mode

`sh install.sh --voice-only` (or `py -3 vsp.py install --voice-only` on Windows) installs Kokoro, onnxruntime, the pinned core Python packages, voice models, and fonts. Intel Macs select this tier automatically, including an x86_64 Python process under Rosetta. Run `python3 vsp.py new my-video`, edit its `project.json`, then `python3 vsp.py voice my-video` and `python3 vsp.py audio my-video`. On Windows, replace `python3` with `py -3`. The direct `scripts/make_voice.py` and audio mixing scripts also work. `build`, `smoke`, direct stills/render and subtitle QC stop with one explanation: these pins have no Intel Mac Torch video stack or supported Chrome rendering path. Use Apple Silicon macOS 14+ for the full video pipeline.

## Important license notes
- **The word-alignment model (MMS_FA) is CC-BY-NC 4.0: non-commercial use only.** Captions in commercial videos
  need a different aligner (not included).
- Remotion (optional, `--with-remotion`) is free only for individuals and organisations of up to 3 people.
- Check the license of every music, SFX, image or footage file you add; the pack's own sounds are synthesized.

## License and credits
The pack's own code and docs: [MIT](LICENSE). Third-party tools and the projects that inspired parts of the pack
are listed with their licenses in [CREDITS.md](CREDITS.md) and [NOTICE](NOTICE). No third-party code is
vendored except where CREDITS.md says so.
