# Video-Making: a video skill pack for AI coding agents

Skills, scripts and a tested pipeline that let an AI agent (Codex, Claude Code, or any agent that reads
`SKILL.md` files) make narrated, captioned, music-backed videos **entirely from code, with free local tools**:
Kokoro text-to-speech, word-exact karaoke subtitles, canvas animation captured one frame at a time by headless
Chrome, ffmpeg mixing at -14 LUFS, and automatic quality checks.

## Quick start
```bash
git clone https://github.com/namra-030604/Video-Making && cd Video-Making && bash install.sh && bash install.sh verify
bash smoke-test/run.sh            # makes smoke-test/out/project/out/hello-world.mp4 (~7 s) and checks it
bash scripts/new_project.sh my-video && bash scripts/build.sh my-video
```
Agents: follow [AGENT_INSTALL.md](AGENT_INSTALL.md) to install the skills into Codex or Claude.

## What you get
| Folder | Contents |
|---|---|
| `skills/` | 11 agent skills (see below), each a folder with a `SKILL.md` |
| `scripts/` | the pipeline: `make_voice.py`, `align_words.py`, `make_audio.py`, `stills.mjs`, `render.mjs`, `subtitle_qc.mjs`, `qc_final.py`, `framediff.py`, `build.sh`, `new_project.sh` |
| `lib/browser.mjs` | a small dependency-free Chrome DevTools driver (no npm packages needed) |
| `examples/hello-world/` | a complete 540x960 narrated scene to copy |
| `smoke-test/run.sh` | end-to-end test of the whole pipeline |
| `install.sh` | installs and verifies everything (project-local `.venv`, cache in `~/.cache/video-skill-pack`) |

Skills: `video-skill-pack` (router), `video-production-standard`, `script-writing`, `voice-and-audio`,
`subtitles-karaoke`, `motion-studio`, `motion-graphics` (18 effect guides + `fx.js`), `vertical-9-16-framing`,
`short-form-editing`, `qc-and-render`, `lessons-from-failures`.

## Requirements
- Linux x86_64 (tested on Debian 13). macOS/Windows are not supported by `install.sh` (untested).
- System packages: `python3` (3.10+, with `venv`; tested with 3.13), `node` (18+; tested with 20.19), `ffmpeg` with libx264, `curl`, `unzip`,
  `sha256sum`. `install.sh` prints the `apt-get` command if something is missing (it runs it only with `--apt`).
- About 4 GB free disk and 2 GB free RAM. No GPU, no API keys, no accounts.

### Download sizes (first install, cached afterwards)
| Item | Size |
|---|---|
| Python venv (CPU PyTorch, onnxruntime, kokoro-onnx...) | ~1.1 GB on disk |
| Kokoro v1.0 int8 model + voices | ~120 MB |
| MMS_FA alignment model (skip with `--skip-aligner`) | ~1.26 GB |
| chrome-headless-shell 156.0.8078.47 (only if no usable Chrome) | ~126 MB zip, ~270 MB unpacked |
| Inter + Caveat fonts | ~1.3 MB |

## Important license notes
- **The word-alignment model (MMS_FA) is CC-BY-NC 4.0: non-commercial use only.** Captions in commercial videos
  need a different aligner (not included).
- Remotion (optional, `--with-remotion`) is free only for individuals and organisations of up to 3 people.
- Check the license of every music, SFX, image or footage file you add; the pack's own sounds are synthesized.

## License and credits
The pack's own code and docs: [MIT](LICENSE). Third-party tools and the projects that inspired parts of the pack
are listed with their licenses in [CREDITS.md](CREDITS.md) and [NOTICE](NOTICE). No third-party code is
vendored except where CREDITS.md says so.
