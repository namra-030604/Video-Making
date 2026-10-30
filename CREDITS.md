# Credits and third-party licenses

The pack's own code and docs are MIT ([LICENSE](LICENSE)). The pack **does not vendor** any of the software below:
`install.sh` downloads or installs it on your machine, and each item stays under its own license. Licenses were
checked on 2026-10-29 from the package metadata, the GitHub license API or the project's license page.

## Installed by install.sh (required)
| Component | Version | License | URL | Used for |
|---|---|---|---|---|
| Kokoro-82M model + voices (int8 ONNX, v1.0) | model-files-v1.0 | Apache-2.0 | https://github.com/hexgrad/kokoro , https://huggingface.co/hexgrad/Kokoro-82M | narration voice |
| kokoro-onnx | 0.6.1 | MIT | https://github.com/thewh1teagle/kokoro-onnx | runs Kokoro on CPU (model files from its releases) |
| espeakng-loader | 0.2.4 | MIT (bundles libespeak-ng, GPL-3.0) | https://github.com/thewh1teagle/espeakng-loader | phonemes for Kokoro, espeak fallback voice |
| espeak-ng | bundled in espeakng-loader | GPL-3.0 | https://github.com/espeak-ng/espeak-ng | phonemizer backend |
| phonemizer (dependency of kokoro-onnx) | 3.4.0 | GPL-3.0-or-later | https://github.com/bootphon/phonemizer | text to phonemes |
| onnxruntime | 1.31.0 | MIT | https://onnxruntime.ai | model inference |
| PyTorch (CPU) | 2.11.0+cpu | BSD-3-Clause | https://pytorch.org | alignment model runtime |
| torchaudio | 2.11.0+cpu | BSD-2-Clause | https://github.com/pytorch/audio | MMS_FA forced alignment API |
| **MMS_FA model weights** | torchaudio pipeline | **CC-BY-NC 4.0 (non-commercial)** | https://docs.pytorch.org/audio/stable/generated/torchaudio.pipelines.MMS_FA.html | word timing for captions |
| numpy | 2.5.4 | BSD-3-Clause (and bundled permissive licenses) | https://numpy.org | audio math |
| soundfile | 0.14.0 | BSD-3-Clause | https://github.com/bastibe/python-soundfile | WAV I/O |
| Pillow | 13.0.0 | MIT-CMU | https://python-pillow.org | image checks |
| FFmpeg (system package) | tested 7.1.5 | LGPL-2.1-or-later; builds with libx264 are GPL-2.0-or-later | https://ffmpeg.org/legal.html | encode, mux, loudness, QC |
| chrome-headless-shell (Chrome for Testing) | 156.0.8078.47 | Chromium: BSD-3-Clause plus bundled third-party licenses | https://googlechromelabs.github.io/chrome-for-testing/ , https://chromium.googlesource.com/chromium/src/+/main/LICENSE | frame rendering (downloaded only if no working Chrome) |
| Inter font | google/fonts @ 6157dfaa64 | SIL OFL-1.1 | https://github.com/rsms/inter | subtitles, titles |
| Caveat font | google/fonts @ 6157dfaa64 | SIL OFL-1.1 | https://github.com/googlefonts/caveat | handwritten accents |
The OFL license texts are saved next to the fonts in the cache (`fonts/Inter-OFL.txt`, `fonts/Caveat-OFL.txt`).

## Optional (only with a flag)
| Component | Version | License | URL |
|---|---|---|---|
| puppeteer-core (`--with-puppeteer`) | 25.16.0 | Apache-2.0 | https://github.com/puppeteer/puppeteer |
| hyperframes (`--with-hyperframes`) | 0.8.217 | Apache-2.0 | https://github.com/heygen-com/hyperframes |
| Remotion (`--with-remotion`) | 4.0.539 | Remotion License (source-available; free for individuals, non-profits and for-profit teams of up to 3 people; larger companies need a Company License) | https://www.remotion.dev/license |
| d3-geo / topojson-client / world-atlas (`--with-maps`) | 3.1.1 / 3.1.0 / 2.0.2 | ISC | https://github.com/d3/d3-geo , https://github.com/topojson/topojson-client , https://github.com/topojson/world-atlas |
| Blender (`--with-blender` only checks; never downloaded) | - | GNU GPL | https://www.blender.org/about/license/ |
| Piper TTS (documented alternative, not installed) | - | MIT (rhasspy/piper, archived); GPL-3.0 (OHF-Voice/piper1-gpl); each voice has its own license | https://github.com/rhasspy/piper , https://github.com/OHF-Voice/piper1-gpl |

## Projects that inspired ideas (no code or text copied)
| Project | License | What we learned from it |
|---|---|---|
| heygen-com/hyperframes | Apache-2.0 | HTML compositions rendered deterministically by seeking time |
| Mng-dev-ai/explainer-video | MIT | agent-driven explainer workflow, script -> scenes -> render |
| cymcymcymcym/notes-to-video | MIT | turning notes into narrated scenes |
| justifyman/gpt-js-animations (fork of klsoen/opus-js-animations) | MIT | catalogue of JS canvas animation techniques |
| acelera-agency/html-animation | MIT | HTML/CSS animation patterns for video |
| bestagentkits/motion-video-skill | MIT (uses paid APIs, not adopted) | packaging motion skills for agents |
| remotion-dev/skills | no license file found: link only, nothing borrowed beyond general ideas | agent skills for Remotion |
| vedvyas44/motion-studio | no license file found: link only, ideas only | name and idea of a motion-studio skill |

## Sound and media
All music and SFX made by the pack are synthesized in code (no samples). If you add files from Freesound,
OpenGameArt, Kenney, Openverse or Wikimedia Commons, record each file's license in your project's `assets/CREDITS.md`.
