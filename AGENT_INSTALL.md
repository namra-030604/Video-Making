# AGENT_INSTALL: step-by-step for an AI agent

Follow these steps in order. Do not use sudo unless the user asks; do not edit agent config files such as
`~/.codex/config.toml`; everything installs into this repo (`.venv`, `node_modules`) and one cache folder
(`${VSP_CACHE:-~/.cache/video-skill-pack}`).

## 1. Clone, install, verify
```bash
git clone https://github.com/namra-030604/Video-Making && cd Video-Making && bash install.sh && bash install.sh verify
```
- `install.sh` is idempotent (safe to re-run) and checks every download against a pinned sha256.
- `verify` really runs each part (Kokoro speaks, MMS_FA aligns, Chrome renders a frame, ffmpeg loudnorm...) and
  prints a PASS/FAIL table. Continue only when it ends with `verify: all required components PASS`.
- Options: `--with-chrome` (force the pinned headless Chrome), `--skip-aligner`, `--with-maps`,
  `--with-hyperframes`, `--with-remotion`, `--with-puppeteer`, `--with-blender` (check only), `--apt`.
  `bash install.sh --help` lists them; `bash install.sh uninstall-notes` shows how to remove everything.

Remember the absolute path of the clone: below it is called `$PACK` (`export PACK="$PWD"`).

## 2. The skill (installed by step 1)
There is exactly **one** skill: the folder `video-making/` with one `SKILL.md` (`name: video-making`). It is a
router: it maps the request to a component under `video-making/components/` (the master video orchestration for a
whole video, or one part such as captions, voice, effects, 9:16, rendering). Nothing else in the repo is a skill.

`bash install.sh` ends by running `bash install.sh link-skills`, which:
- auto-detects `~/.codex` and `~/.claude` and creates `~/.codex/skills/video-making` and/or
  `~/.claude/skills/video-making` as a **symlink** to `$PACK/video-making` (so `git pull` updates it);
- prints every path it linked; re-running is safe (`ok (already linked)`);
- falls back to a **copy** if a symlink cannot be made (or with `--copy`); copies contain `PACK_ROOT` and a
  `.vsp-copy` marker, and are refreshed on the next `link-skills` (re-run it after `git pull`);
- **never** replaces a `video-making` folder or symlink it did not create: it warns and leaves it alone.

Options: `--link-codex`, `--link-claude` (create that agent's skills folder even if the agent folder is missing),
`--skills-dir DIR` (for example a project's `.agents/skills` or `.claude/skills`), `--copy`, and `--no-link`
(on `install`, skip linking). Manual fallback: `ln -s "$PACK/video-making" ~/.claude/skills/video-making`.
The skill finds the pack root from `VSP_PACK`, else `video-making/PACK_ROOT` (written by `link-skills`), else
the parent of the skill folder's real path. `verify` checks the skill is linked, that it is the only `SKILL.md`,
that every relative path in the skill docs resolves, and runs the router keyword test.

## 3. Tell the agent where the pack is (AGENTS.md for Codex, CLAUDE.md for Claude)
Add to the project's or the global instructions file, with the real path filled in:
```markdown
## Video making
- The video skill pack is installed at PACK=<absolute path of the Video-Making clone>.
- For any video task, load the `video-making` skill (its SKILL.md is a router) and follow the component it points to.
- Run `bash $PACK/install.sh verify` before the first video of a session.
- Make projects with `bash $PACK/scripts/new_project.sh <dir>` and build with `bash $PACK/scripts/build.sh <dir>`.
- A video is finished only when `qc_final.py` prints OVERALL PASS. Free local voices only.
```

## 4. Smoke test
```bash
bash "$PACK/smoke-test/run.sh"          # add --clean to start from scratch
```
Makes a ~7 s 540x960 narrated clip through the whole pipeline and ends with `OVERALL PASS`. On this pack's test
machine (8 cores) the first run took a few minutes, mostly model loading. Re-running skips finished stages.

## 5. Make a first video
```bash
bash "$PACK/scripts/new_project.sh" ~/videos/first-video
# 1. edit project.json: "lines" (one sentence each), width/height (1080x1920 vertical or 1920x1080), "subtitles"
# 2. edit index.html: draw your scene in renderFrame(t) (keep it a pure function of t)
node "$PACK/scripts/stills.mjs" --project ~/videos/first-video --n 8 --scan   # look at out/stills/contact.png
bash "$PACK/scripts/build.sh" ~/videos/first-video
```
The router sends a whole-video request to `video-making/components/master-video/MASTER.md`, which walks the
phases and opens `script-writing`, `voice-and-audio`, `motion-graphics` and the rest in order.

## 6. Troubleshooting
| Symptom | Fix |
|---|---|
| `headless Chrome render` FAIL, or Chrome exits with policy errors | A managed/system Chrome is blocked or too old: `bash install.sh --with-chrome` downloads the pinned chrome-headless-shell; or set `CHROME=/path/to/chrome`. |
| Chrome fails with `error while loading shared libraries` | Run the `ldd ... | grep 'not found'` command that `install.sh` prints; the Debian package list is in `chrome-headless-shell-linux64/deb.deps` inside the cache. Install those packages (needs admin rights). |
| `No module named venv` / `ensurepip is not available` | Install `python3-venv`. `install.sh` falls back to `pip install --user` only if a venv cannot be made. |
| `ffmpeg has no libx264` | Install the distro `ffmpeg` package (Debian/Ubuntu builds include libx264), or a static build and put it first on PATH. |
| `only N MB RAM available` | Close other heavy programs (only your own), then re-run; finished parts are kept. Keep `render.threads` at 1-2. |
| Alignment below 97% | Spell numbers and symbols as words; remove words the voice skips; check `audio/line_NN.wav`. |
| Captions out of the safe zone | Lower `subtitles.font_px` or widen `safe_side`; see the `subtitles-karaoke` component. |
| `stills.mjs --check` FAIL | The scene uses timers, `Math.random`, `Date.now`, CSS animations, or state from earlier frames. Make it a pure function of t. |
| Download fails | Re-run `install.sh` (each download is retried 3 times; finished, checksum-verified files are kept); behind a proxy set `HTTPS_PROXY`. |

## 7. Rules for agents using this pack
1. Free local voices only (Kokoro, Piper, espeak-ng). Never clone a real person's voice; no paid APIs.
2. Speed 1.0, no time-stretch; fit duration by editing words.
3. Look at stills before every full render; never ship without `qc_final.py` OVERALL PASS.
4. One heavy process at a time; run `free -h` first; stop only processes you started.
5. Record every third-party asset with its license in `assets/CREDITS.md`; prefer synthesized sound.
6. MMS_FA alignment is CC-BY-NC 4.0: tell the user before using it for commercial work.
7. Report honestly what was not checked.

## 8. Not tested yet
- `install.sh --apt` on a clean machine (the apt package list is from documentation, not a fresh-VM run).
- The `pip install --user` fallback when venv is unavailable.
- `--with-remotion`, `--with-hyperframes`, `--with-blender` (Blender is never downloaded; install it yourself from
  blender.org) and `--with-puppeteer` (needs Node >= 22.12).
- Map scenes with `--with-maps` at render time.
- Skill discovery by a real Codex or Claude Code session (here only the files and links were checked); whether an
  agent follows a symlinked skill folder may differ by version - use `--copy` if it does not.
- The router test is a keyword check of the routing table, not a test of how an LLM actually routes.
- `--link-claude` on a machine with Claude Code installed (only `--skills-dir` and `~/.codex/skills` were exercised).
- macOS, Windows, ARM Linux.
