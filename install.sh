#!/usr/bin/env bash
# install.sh - set up the video skill pack on Debian/Ubuntu-like Linux (x86_64). Idempotent: safe to re-run.
#
#   bash install.sh [install] [options]   install everything into ./.venv and the cache dir (default)
#   bash install.sh verify                really test each component, print a PASS/FAIL table, exit 1 on any FAIL
#   bash install.sh link-skills [opts]    install ONLY the single `video-making` skill into your agent(s)
#                                         (also runs at the end of a default install)
#   bash install.sh uninstall-notes       print what was installed and how to remove it (removes nothing)
#
# Options (link-skills; default = auto-detect: ~/.codex -> ~/.codex/skills, ~/.claude -> ~/.claude/skills):
#   --link-codex / --link-claude  link into that agent even if its folder does not exist yet (creates skills/)
#   --skills-dir DIR   link into DIR/video-making instead (e.g. a project's .agents/skills or .claude/skills)
#   --copy             copy instead of symlink (copy is also the automatic fallback if a symlink fails)
#   --relink           repoint an existing video-making symlink that targets ANOTHER clone of this pack (or a
#                      deleted one) to this clone. Symlinks or folders that are not this pack are never touched.
#   --no-link          default install skips linking
#
# Options (install):
#   --apt              also install missing system packages with apt-get. Only used if you are root or have
#                      password-less sudo. Without this flag the script only PRINTS the apt command to run.
#   --with-chrome      download the pinned chrome-headless-shell (Chrome for Testing) even if a system Chrome works
#   --no-chrome        never download Chrome (use a system Chrome or $CHROME only)
#   --with-maps        npm: d3-geo, topojson-client, world-atlas (map scenes)
#   --with-puppeteer   npm: puppeteer-core (only if you prefer Puppeteer over the built-in driver; needs Node >= 22.12)
#   --with-hyperframes npm: hyperframes (HeyGen's HTML-to-video CLI, Apache-2.0) - optional alternative renderer
#   --with-remotion    npm: remotion + @remotion/cli (Remotion License: companies above a size need a paid licence)
#   --with-blender     check for Blender (3D). Blender is never downloaded by this script; see AGENT_INSTALL.md
#   --skip-aligner     do not pre-download the ~1.2 GB MMS_FA alignment model
#
# Environment: VSP_CACHE (default ${XDG_CACHE_HOME:-~/.cache}/video-skill-pack) holds models, fonts and Chrome.
# Rules: no sudo unless --apt is passed; every download is pinned to a version and checked with sha256
# (the PyTorch/PyPI wheels are pinned by version and verified by pip); nothing is piped into a shell.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
CACHE="${VSP_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/video-skill-pack}"
VENV="$HERE/.venv"
STATE="$HERE/.vsp-state"            # remembers which python to use (venv or user site)
export TORCH_HOME="$CACHE/torch"

# ---- pinned artifacts (url  sha256  size) -----------------------------------------------------------------
KOKORO_BASE="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
MMS_FA_SHA256=20ef12963ab4924bef49ac4fc7f58ad5da2ee43b2c11bc8c853c9b90ecdbc680  # 1,262,047,414 bytes
KOKORO_MODEL_SHA="6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb"   # kokoro-v1.0.int8.onnx, 92,361,271 bytes
KOKORO_VOICES_SHA="bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d"  # voices-v1.0.bin, 28,214,398 bytes
FONTS_COMMIT="6157dfaa640ca5738b4d1a7070fe389c3036d7fc"                               # github.com/google/fonts
FONTS=(
  "Inter.ttf|ofl/inter/Inter%5Bopsz,wght%5D.ttf|29160a80ff49ddcab2c97711247e08b1fab27a484a329ce8b813d820dc559031"
  "Inter-OFL.txt|ofl/inter/OFL.txt|5b9321a4298cfeb6b34354164a1c3afc3db114569984c502b9b35d988fd58c57"
  "Caveat.ttf|ofl/caveat/Caveat%5Bwght%5D.ttf|0bdb6b660482d31531b3945849fba5916b3ef8695da7024a9e6b9ee3c4157988"
  "Caveat-OFL.txt|ofl/caveat/OFL.txt|1f9d81d094273d82f3898a1ee8b598a717d050ecbf5ff7bede105b704880157b"
)
CHROME_VERSION="156.0.8078.47"                                                         # Chrome for Testing
CHROME_ZIP_SHA="0d5acc62c3e213f8c87d3c298d66ffcf9a236d12ea4b9f85318bf85dbc279daa"     # chrome-headless-shell-linux64.zip, 125,799,226 bytes
TORCH_INDEX="https://download.pytorch.org/whl/cpu"
NPM_MAPS="d3-geo@3.1.1 topojson-client@3.1.0 world-atlas@2.0.2"
NPM_PUPPETEER="puppeteer-core@25.16.0"
NPM_HYPERFRAMES="hyperframes@0.8.217"
NPM_REMOTION="remotion@4.0.539 @remotion/cli@4.0.539"
APT_PKGS="ffmpeg python3 python3-venv python3-pip nodejs npm unzip curl ca-certificates fonts-dejavu-core"

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWARN:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }
retry() { local n=0; until "$@"; do n=$((n+1)); [ $n -ge 3 ] && return 1; warn "retrying ($n/3): $*"; sleep $((n*3)); done; }

fetch() {  # fetch URL DEST SHA256 - download to DEST.part, verify, then move into place. Skips if DEST already verifies.
  local url="$1" dest="$2" sha="$3"
  if [ -f "$dest" ] && echo "$sha  $dest" | sha256sum -c --status; then echo "  ok (cached) $(basename "$dest")"; return 0; fi
  mkdir -p "$(dirname "$dest")"
  retry curl -fL --proto '=https' --tlsv1.2 --retry 3 --connect-timeout 20 -sS -o "$dest.part" "$url" || die "download failed: $url"
  echo "$sha  $dest.part" | sha256sum -c --status || { rm -f "$dest.part"; die "checksum mismatch for $url (expected $sha)"; }
  mv "$dest.part" "$dest"; echo "  downloaded + verified $(basename "$dest")"
}

py() { local p; p="$(cat "$STATE/python" 2>/dev/null || echo python3)"; "$p" "$@"; }

# ---- options -------------------------------------------------------------------------------------------------
CMD=install; RELINK=0; LINK=auto; LINK_CODEX=0; LINK_CLAUDE=0; SKILLS_DIR=""; COPY=0; APT=0; WITH_CHROME=auto; MAPS=0; PUPPETEER=0; HYPERFRAMES=0; REMOTION=0; BLENDER=0; SKIP_ALIGNER=0
NEXT_DIR=0
for a in "$@"; do
  if [ $NEXT_DIR = 1 ]; then SKILLS_DIR="$a"; NEXT_DIR=0; continue; fi
  case "$a" in
  install|verify|uninstall-notes|link-skills) CMD="$a";;
  --link-codex) LINK_CODEX=1;; --link-claude) LINK_CLAUDE=1;; --skills-dir) NEXT_DIR=1;; --skills-dir=*) SKILLS_DIR="${a#*=}";;
  --copy) COPY=1;; --no-link) LINK=no;; --relink) RELINK=1;;
  --apt) APT=1;; --with-chrome) WITH_CHROME=yes;; --no-chrome) WITH_CHROME=no;;
  --with-maps) MAPS=1;; --with-puppeteer) PUPPETEER=1;; --with-hyperframes) HYPERFRAMES=1;; --with-remotion) REMOTION=1;;
  --with-blender) BLENDER=1;; --skip-aligner) SKIP_ALIGNER=1;;
  -h|--help) awk 'NR>1 && /^#/{print; next} NR>1{exit}' "$0"; exit 0;;
  *) die "unknown argument: $a (see: bash install.sh --help)";;
esac; done
[ $NEXT_DIR = 1 ] && die "--skills-dir needs a folder"

# ---- install -------------------------------------------------------------------------------------------------
step_preflight() {
  say "Preflight"
  [ "$(uname -s)" = Linux ] || die "Linux only (tested on Debian 13 x86_64)."
  [ "$(uname -m)" = x86_64 ] || warn "only tested on x86_64; Chrome download and torch wheels may not exist for $(uname -m)"
  local free_kb; free_kb=$(df -Pk "$HERE" | awk 'NR==2{print $4}')
  [ "$free_kb" -gt 4000000 ] || warn "less than 4 GB free disk here; the install needs about 3.5 GB (torch ~0.8 GB, aligner model ~1.2 GB, Chrome ~0.3 GB)"
  have free && free -h | sed -n '1,2p'
  local missing=()
  for b in python3 node npm ffmpeg ffprobe curl sha256sum unzip; do have "$b" || missing+=("$b"); done
  if [ ${#missing[@]} -gt 0 ]; then
    if [ $APT = 1 ]; then
      if [ "$(id -u)" = 0 ]; then apt-get update && apt-get install -y $APT_PKGS
      elif have sudo && sudo -n true 2>/dev/null; then sudo apt-get update && sudo apt-get install -y $APT_PKGS
      else die "missing: ${missing[*]}. --apt was given but you are not root and sudo needs a password. Run yourself:  sudo apt-get install -y $APT_PKGS"; fi
    else
      die "missing: ${missing[*]}. Install them, e.g.:  sudo apt-get install -y $APT_PKGS   (or re-run with --apt if you have sudo)"
    fi
  fi
  python3 -c 'import sys; assert sys.version_info >= (3, 10)' || die "Python >= 3.10 needed (found $(python3 --version))"
  node -e 'process.exit(+process.versions.node.split(".")[0] >= 18 ? 0 : 1)' || die "Node >= 18 needed (found $(node --version))"
  local enc; enc=$(ffmpeg -hide_banner -encoders 2>/dev/null || true); [[ "$enc" == *libx264* ]] || die "your ffmpeg has no libx264 encoder; install the distro ffmpeg package"
}

step_python() {
  say "Python packages (pinned)"
  mkdir -p "$STATE"
  if [ -x "$VENV/bin/python" ] || python3 -m venv "$VENV" 2>/dev/null; then
    echo "$VENV/bin/python" > "$STATE/python"
    retry "$VENV/bin/python" -m pip install -q --upgrade "pip==26.2.2" || warn "could not upgrade pip; continuing"
    retry "$VENV/bin/python" -m pip install -q -r requirements.txt || die "pip install failed (requirements.txt)"
    retry "$VENV/bin/python" -m pip install -q --index-url "$TORCH_INDEX" -r requirements-torch.txt || die "pip install failed (torch CPU wheels from $TORCH_INDEX)"
  else
    # Fallback rule: no venv module (python3-venv missing) -> install into the user site. On Debian 12+/Ubuntu 23.04+
    # pip refuses this without --break-system-packages (PEP 668); --user keeps it out of system directories.
    warn "python3 -m venv is unavailable (install python3-venv for a clean venv). Falling back to pip --user --break-system-packages."
    echo "python3" > "$STATE/python"
    retry python3 -m pip install -q --user --break-system-packages -r requirements.txt || die "pip --user install failed"
    retry python3 -m pip install -q --user --break-system-packages --index-url "$TORCH_INDEX" -r requirements-torch.txt || die "pip --user torch install failed"
  fi
}

step_models() {
  say "Kokoro voice model (Apache-2.0 weights, via the kokoro-onnx v1.0 release, ~120 MB)"
  fetch "$KOKORO_BASE/kokoro-v1.0.int8.onnx" "$CACHE/models/kokoro-v1.0.int8.onnx" "$KOKORO_MODEL_SHA"
  fetch "$KOKORO_BASE/voices-v1.0.bin" "$CACHE/models/voices-v1.0.bin" "$KOKORO_VOICES_SHA"
  if [ $SKIP_ALIGNER = 0 ]; then
    say "MMS_FA forced-alignment model (torchaudio, ~1.2 GB, downloaded once from Meta's official host dl.fbaipublicfiles.com)"
    retry py -c 'import torchaudio; torchaudio.pipelines.MMS_FA.get_model(dl_kwargs={"progress": False}); print("  ok MMS_FA cached in", __import__("os").environ["TORCH_HOME"])' || die "MMS_FA download failed"
    # upstream publishes no checksum; this sha256 was recorded from the file torchaudio 2.11 downloaded on 2026-10-29
    local mf="$TORCH_HOME/hub/checkpoints/model.pt"
    [[ "$(sha256sum "$mf" | cut -d' ' -f1)" == "$MMS_FA_SHA256" ]] || die "MMS_FA model.pt checksum mismatch - delete $mf and re-run"
  fi
  say "OFL fonts (Inter, Caveat) from github.com/google/fonts @ ${FONTS_COMMIT:0:10}"
  for f in "${FONTS[@]}"; do IFS='|' read -r name path sha <<<"$f"; fetch "https://raw.githubusercontent.com/google/fonts/$FONTS_COMMIT/$path" "$CACHE/fonts/$name" "$sha"; done
}

chrome_ok() { local o; o=$(node "$HERE/lib/selftest.mjs" 2>/dev/null || true); [[ "$o" == *'"ok":true'* ]]; }
step_chrome() {
  [ $WITH_CHROME = no ] && { say "Chrome: skipped (--no-chrome)"; return; }
  if [ $WITH_CHROME = auto ] && chrome_ok; then say "Chrome: existing browser renders correctly ($(node lib/selftest.mjs | sed 's/.*"chrome":"\([^"]*\)".*/\1/'))"; return; fi
  say "Chrome: installing pinned chrome-headless-shell $CHROME_VERSION (Chrome for Testing, ~126 MB zip)"
  local dir="$CACHE/chrome/$CHROME_VERSION"
  if [ ! -x "$dir/chrome-headless-shell-linux64/chrome-headless-shell" ]; then
    fetch "https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chrome-headless-shell-linux64.zip" "$CACHE/chrome/chs-$CHROME_VERSION.zip" "$CHROME_ZIP_SHA"
    rm -rf "$dir.part" && mkdir -p "$dir.part" && unzip -q "$CACHE/chrome/chs-$CHROME_VERSION.zip" -d "$dir.part" && mv "$dir.part" "$dir" && rm -f "$CACHE/chrome/chs-$CHROME_VERSION.zip"
  fi
  chrome_ok || { warn "chrome-headless-shell does not start. Missing shared libraries? Print them with:  ldd $dir/chrome-headless-shell-linux64/chrome-headless-shell | grep 'not found'   (Debian package list: $dir/chrome-headless-shell-linux64/deb.deps)"; die "no working headless Chrome"; }
}

step_npm() {
  local pkgs=""
  [ $MAPS = 1 ] && pkgs="$pkgs $NPM_MAPS"; [ $PUPPETEER = 1 ] && pkgs="$pkgs $NPM_PUPPETEER"
  [ $HYPERFRAMES = 1 ] && pkgs="$pkgs $NPM_HYPERFRAMES"; [ $REMOTION = 1 ] && pkgs="$pkgs $NPM_REMOTION"
  [ -z "$pkgs" ] && { say "npm: no optional modules requested (the renderer itself needs no npm packages)"; return; }
  say "npm (project-local ./node_modules, exact versions):$pkgs"
  [ $REMOTION = 1 ] && warn "Remotion is NOT free for every company: read https://www.remotion.dev/license before commercial use."
  retry npm install --no-audit --no-fund --save-exact --prefix "$HERE" $pkgs || die "npm install failed"
}

step_blender() {
  [ $BLENDER = 1 ] || return 0
  if have blender; then say "Blender found: $(blender --version 2>/dev/null | head -1)"; else
    warn "Blender not found. It is optional (3D scenes only). Install from your distro (sudo apt-get install blender) or the official site https://www.blender.org/download/ (verify the published SHA256)."; fi
}

do_install() {
  step_preflight; step_python; step_models; step_chrome; step_npm; step_blender
  py -m pip freeze --all 2>/dev/null | grep -v '^-e ' > "$STATE/pip-freeze.txt" || true
  if [ $LINK = no ]; then say "Skipping skill linking (--no-link). Later: bash install.sh link-skills"; else do_link_skills; fi
  say "Done. Now run:  bash install.sh verify   then   bash smoke-test/run.sh"
}

# ---- link-skills: install the ONE skill folder (video-making/) into agent skill dirs ----------------------------
SKILL_SRC="$HERE/video-making"
skill_targets() {  # prints one skills dir per line
  if [ -n "$SKILLS_DIR" ]; then echo "$SKILLS_DIR"; return; fi
  local any=0
  if [ $LINK_CODEX = 1 ] || { [ $LINK_CLAUDE = 0 ] && [ -d "$HOME/.codex" ]; }; then echo "$HOME/.codex/skills"; any=1; fi
  if [ $LINK_CLAUDE = 1 ] || { [ $LINK_CODEX = 0 ] && [ -d "$HOME/.claude" ]; }; then echo "$HOME/.claude/skills"; any=1; fi
  return 0
}
copy_skill() {  # copy_skill DEST - our own copy, marked so we can refresh it later
  rm -rf "$1.vsp-tmp" && cp -R "$SKILL_SRC" "$1.vsp-tmp" && echo "$HERE" > "$1.vsp-tmp/PACK_ROOT" && echo "copied by video-making install.sh" > "$1.vsp-tmp/.vsp-copy" \
    && { [ ! -e "$1" ] || rm -rf "$1"; } && mv "$1.vsp-tmp" "$1"
}
is_pack_skill() {  # is_pack_skill DIR - DIR is the video-making folder of some clone of this pack
  [ -f "$1/SKILL.md" ] && grep -q '^name: video-making$' "$1/SKILL.md" && [ -f "$1/../install.sh" ]
}
link_one() {  # link_one SKILLS_DIR
  local dir="$1" dest="$1/video-making"
  mkdir -p "$dir" || { warn "cannot create $dir - skipped"; return 0; }
  if [ -L "$dest" ]; then
    if [ "$(readlink -f "$dest")" = "$(readlink -f "$SKILL_SRC")" ]; then echo "  ok (already linked) $dest -> $SKILL_SRC"; return 0; fi
    local old; old="$(readlink "$dest")"
    if [ ! -e "$dest" ] || is_pack_skill "$dest"; then   # dangling, or another clone of this same pack
      if [ $RELINK = 1 ]; then ln -sfn "$SKILL_SRC" "$dest" && echo "  relinked $dest -> $SKILL_SRC (was -> $old)"; return 0; fi
      if [ ! -e "$dest" ]; then warn "$dest is a broken symlink (-> $old). Kept. Point it here with: bash install.sh link-skills --relink"
      else echo "  kept $dest -> $old (another clone of this pack; it works). To use this clone: bash install.sh link-skills --relink"; fi
      return 0
    fi
    warn "$dest is a symlink to $old, which is not this pack. Left it alone. Remove it yourself and re-run: bash install.sh link-skills"; return 0
  fi
  if [ -e "$dest" ]; then
    if [ -f "$dest/.vsp-copy" ]; then copy_skill "$dest" && echo "  refreshed copy $dest (PACK_ROOT=$HERE)"; return 0; fi
    warn "$dest already exists and was not made by this installer. Left it alone. Move it away and re-run: bash install.sh link-skills"; return 0
  fi
  if [ $COPY = 0 ] && ln -s "$SKILL_SRC" "$dest" 2>/dev/null && [ -f "$dest/SKILL.md" ]; then echo "  linked $dest -> $SKILL_SRC"; return 0; fi
  [ -L "$dest" ] && rm -f "$dest"
  copy_skill "$dest" && echo "  copied $SKILL_SRC -> $dest (PACK_ROOT=$HERE; re-run link-skills after git pull)" || warn "could not link or copy into $dest"
}
do_link_skills() {
  say "Installing the single skill 'video-making' (router -> master video -> components)"
  echo "$HERE" > "$SKILL_SRC/PACK_ROOT"     # lets the skill find the pack root (gitignored)
  local t n=0; while IFS= read -r t; do [ -n "$t" ] && { link_one "$t"; n=$((n+1)); }; done < <(skill_targets)
  if [ $n = 0 ]; then
    echo "  no ~/.codex or ~/.claude found - nothing linked. Use: bash install.sh link-skills --link-codex | --link-claude | --skills-dir DIR"
  fi
  echo "  agents should load ONLY video-making/SKILL.md; it routes to everything else. Or set VSP_PACK=$HERE"
}
skill_status() {  # for verify: where is the skill installed?
  local d found="" bad="" other=""
  for d in "$HOME/.codex/skills" "$HOME/.claude/skills" ${SKILLS_DIR:+"$SKILLS_DIR"}; do
    local x="$d/video-making"
    if [ -L "$x" ] && [ "$(readlink -f "$x")" = "$(readlink -f "$SKILL_SRC")" ]; then found="$found ${x/#"$HOME"/\~}(link)"
    elif [ -L "$x" ] && [ ! -e "$x" ]; then bad="$bad ${x/#"$HOME"/\~}(broken link: run link-skills --relink)"
    elif [ -L "$x" ] && is_pack_skill "$x"; then other="$other ${x/#"$HOME"/\~} -> $(readlink "$x")"
    elif [ -f "$x/.vsp-copy" ] && [ -f "$x/SKILL.md" ]; then found="$found ${x/#"$HOME"/\~}(copy)"
    elif [ -e "$x" ]; then bad="$bad ${x/#"$HOME"/\~}"; fi
  done
  if [ -n "$found" ]; then row "skill installed" PASS "video-making at$found"
  elif [ -n "$other" ]; then row "skill installed" WARN "linked to another clone:$other (works; link-skills --relink to use this one)"
  elif [ -n "$bad" ]; then row "skill installed" FAIL "not usable (not made by this installer, or broken):$bad"
  elif [ -d "$HOME/.codex" ] || [ -d "$HOME/.claude" ]; then row "skill installed" FAIL "not linked yet: bash install.sh link-skills"
  else row "skill installed" SKIP "no ~/.codex or ~/.claude; run link-skills --skills-dir DIR"; fi
}

# ---- verify --------------------------------------------------------------------------------------------------
ROWS=(); FAILS=0
row() { ROWS+=("$1|$2|$3"); [ "$2" = FAIL ] && FAILS=$((FAILS+1)); return 0; }
check() { local name="$1"; shift; local out; if out=$("$@" 2>&1); then row "$name" PASS "$(echo "$out" | tail -1 | cut -c1-90)"; else row "$name" FAIL "$(echo "$out" | tail -1 | cut -c1-90)"; fi; }
chrome_check() { local o; o=$(node "$HERE/lib/selftest.mjs" 2>&1) || { echo "$o"; return 1; }; echo "$o" | grep -q '"ok":true' || { echo "$o"; return 1; }; echo "$o" | sed 's/.*"chrome":"\([^"]*\)".*"font":"\([^"]*\)".*/\1 renders frames (font: \2)/' | sed "s#$HOME#~#"; }
do_verify() {
  say "Verifying (each component is exercised, not just located)"
  check "python >= 3.10"       py -c 'import sys; assert sys.version_info >= (3,10), sys.version; print(sys.version.split()[0], sys.executable)'
  check "python packages"      py -c 'import kokoro_onnx, onnxruntime, numpy, soundfile, PIL, torch, torchaudio; from importlib.metadata import version as v; print("kokoro-onnx", v("kokoro-onnx"), "torch", torch.__version__, "torchaudio", torchaudio.__version__)'
  check "node >= 18"           node -e 'if (+process.versions.node.split(".")[0] < 18) throw Error(process.version); console.log(process.version)'
  check "ffmpeg (libx264+aac)" bash -c 'ffmpeg -hide_banner -loglevel error -f lavfi -i testsrc2=s=64x64:r=30:d=0.5 -f lavfi -i sine=d=0.5 -c:v libx264 -c:a aac -shortest -y /tmp/vsp-verify.mp4 && ffmpeg -version | head -1 | cut -d" " -f1-3'
  check "ffprobe"              bash -c 'n=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 /tmp/vsp-verify.mp4); [ "$n" = 15 ] && echo "counted $n frames"'
  check "loudnorm filter"      bash -c 'ffmpeg -hide_banner -nostats -i /tmp/vsp-verify.mp4 -af loudnorm=I=-14:TP=-1.5:print_format=json -f null - 2>&1 | grep -q input_i && echo "two-pass loudness measurement works"'
  check "kokoro model sha256"  bash -c "echo '$KOKORO_MODEL_SHA  $CACHE/models/kokoro-v1.0.int8.onnx' | sha256sum -c --status && echo '$KOKORO_VOICES_SHA  $CACHE/models/voices-v1.0.bin' | sha256sum -c --status && echo 'model + voices match pinned sha256'"
  check "MMS_FA model sha256"  bash -c "echo '$MMS_FA_SHA256  ${TORCH_HOME}/hub/checkpoints/model.pt' | sha256sum -c --status && echo 'model.pt matches the recorded sha256'"
  check "kokoro speaks"        py -c "
from kokoro_onnx import Kokoro; import numpy as np, soundfile as sf
k=Kokoro('$CACHE/models/kokoro-v1.0.int8.onnx','$CACHE/models/voices-v1.0.bin'); a,sr=k.create('Testing one two three.',voice='af_heart',lang='en-us',speed=1.0)
a=np.asarray(a); assert sr==24000 and len(a)>sr*0.6 and np.abs(a).max()>0.05, (sr,len(a)); sf.write('/tmp/vsp-verify.wav',a,sr); print(f'af_heart: {len(a)/sr:.2f}s of speech')"
  check "MMS_FA alignment"     py -c "
import os,torch,torchaudio,soundfile as sf
a,sr=sf.read('/tmp/vsp-verify.wav',dtype='float32'); x=torchaudio.functional.resample(torch.from_numpy(a),sr,16000)
b=torchaudio.pipelines.MMS_FA; m=b.get_model(); tok=b.get_tokenizer(); al=b.get_aligner()
with torch.inference_mode(): e,_=m(x.unsqueeze(0))
sp=al(e[0],tok(['testing','one','two','three'])); st=len(a)/sr/e.shape[1]
ts=[round(s[0].start*st,2) for s in sp]; assert len(ts)==4 and ts==sorted(ts), ts; print('word starts', ts)"
  check "fonts sha256"         bash -c "$(for f in "${FONTS[@]}"; do IFS='|' read -r n p s <<<"$f"; printf "echo '%s  %s' | sha256sum -c --status && " "$s" "$CACHE/fonts/$n"; done) echo 'Inter + Caveat (OFL) match pinned sha256'"
  check "headless Chrome render" chrome_check
  local df_kb; df_kb=$(df -Pk "$HERE" | awk 'NR==2{print $4}'); if [ "$df_kb" -gt 1000000 ]; then row "disk space" PASS "$((df_kb/1024/1024)) GB free"; else row "disk space" FAIL "under 1 GB free"; fi
  local mem; mem=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo); if [ "$mem" -gt 1500 ]; then row "RAM available" PASS "$mem MB"; else row "RAM available" FAIL "$mem MB (need >= 1.5 GB free)"; fi
  check "single SKILL.md + links" py "$HERE/scripts/check_links.py"
  check "router keyword test"  py "$HERE/scripts/router_test.py"
  skill_status
  # optional modules: SKIP when not installed
  for m in d3-geo puppeteer-core hyperframes remotion; do
    if [ -f "$HERE/node_modules/$m/package.json" ]; then check "optional: $m" node -e "console.log(require('$HERE/node_modules/$m/package.json').version)"; else row "optional: $m" SKIP "not installed (flag not used)"; fi
  done
  if have blender; then check "optional: blender" bash -c 'blender --version | head -1'; else row "optional: blender" SKIP "not installed (optional, 3D only)"; fi
  rm -f /tmp/vsp-verify.mp4 /tmp/vsp-verify.wav
  printf '\n%-24s %-5s %s\n' COMPONENT RESULT DETAIL; printf '%-24s %-5s %s\n' ------------------------ ----- ------
  for r in "${ROWS[@]}"; do IFS='|' read -r a b c <<<"$r"; printf '%-24s %-5s %s\n' "$a" "$b" "$c"; done
  echo; if [ $FAILS -gt 0 ]; then echo "verify: $FAILS FAIL(s). Fix them (see AGENT_INSTALL.md > Troubleshooting) and re-run."; exit 1; else echo "verify: all required components PASS"; fi
}

do_uninstall_notes() {
  cat <<NOTES
Nothing is removed automatically. The pack installed only these things:
  $VENV                      Python virtual environment          ->  rm -rf "$VENV"
  $STATE                     which python to use + pip freeze    ->  rm -rf "$STATE"
  $HERE/node_modules         optional npm modules (if any)       ->  rm -rf "$HERE/node_modules" "$HERE/package-lock.json"
  $CACHE                     models, aligner, fonts, Chrome      ->  rm -rf "$CACHE"
If the venv fallback was used, packages are in your user site: python3 -m pip uninstall --break-system-packages -r requirements.txt -r requirements-torch.txt
The skill link/copy made by link-skills (only these, if present):
  ~/.codex/skills/video-making  ~/.claude/skills/video-making  (or DIR/video-making if you used --skills-dir)
  -> rm ~/.codex/skills/video-making        (symlink)   or   rm -rf ~/.codex/skills/video-making   (copy with .vsp-copy)
apt packages were only installed if you passed --apt; remove them with apt-get if you want.
NOTES
}

case "$CMD" in install) do_install;; verify) do_verify;; link-skills) do_link_skills;; uninstall-notes) do_uninstall_notes;; esac
