#!/usr/bin/env bash
# smoke-test/run.sh : make a ~6 s 540x960 original clip ("Hello, video skill pack") through the WHOLE pipeline:
#   Kokoro voice -> MMS_FA word alignment -> synthesized bed + SFX + -14 LUFS loudness -> review stills ->
#   headless-Chrome frames in verified parts -> ffmpeg mux -> subtitle QC -> final QC gates.
# Restart-safe: everything goes to smoke-test/out/, each finished stage is recorded in out/PROGRESS.md and
# skipped on re-run (delete smoke-test/out/ or pass --clean to start over). One heavy step at a time.
set -euo pipefail
PACK="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$PACK/smoke-test/out"; P="$OUT/project"
[ "${1:-}" = "--clean" ] && rm -rf "$OUT"
[ -f "$PACK/.vsp-state/python" ] || { echo "Run 'bash install.sh' first (no .vsp-state/python found)."; exit 1; }
PY="$(cat "$PACK/.vsp-state/python")"
export VSP_CACHE="${VSP_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/video-skill-pack}"
export TORCH_HOME="$VSP_CACHE/torch"

echo "== free -h (memory check before anything heavy)"; free -h
avail=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
[ "$avail" -lt 1500 ] && { echo "Only ${avail} MB RAM available; need about 1.5 GB. Close something and re-run."; exit 1; }

mkdir -p "$OUT"
if [ ! -f "$P/project.json" ]; then
  mkdir -p "$P"; cp "$PACK/examples/hello-world/project.json" "$PACK/examples/hello-world/index.html" "$P/"
  printf '# PROGRESS (smoke test)\n\nRe-run `bash smoke-test/run.sh` to continue; finished stages are skipped.\n\n' > "$OUT/PROGRESS.md"
fi
log() { printf -- '- %s %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$1" >> "$OUT/PROGRESS.md"; }

stage() {  # stage <name> <cmd...> : run once, mark done
  local name="$1"; shift
  if [ -f "$OUT/.done-$name" ]; then echo "== $name: already done (skipped)"; return 0; fi
  echo "== $name"; local t0=$SECONDS
  if "$@"; then touch "$OUT/.done-$name"; log "$name done in $((SECONDS - t0)) s"
  else log "$name FAILED (fix, then re-run; finished stages are skipped)"; echo "!! $name failed"; exit 1; fi
}

stage voice      "$PY" "$PACK/scripts/make_voice.py"  --project "$P"
stage align      "$PY" "$PACK/scripts/align_words.py" --project "$P"
stage audio      "$PY" "$PACK/scripts/make_audio.py"  --project "$P"
stage stills     node "$PACK/scripts/stills.mjs" --project "$P" --n 6 --scan
stage render     node "$PACK/scripts/render.mjs" --project "$P"
stage subtitles  node "$PACK/scripts/subtitle_qc.mjs" --project "$P"
stage qc         "$PY" "$PACK/scripts/qc_final.py" --project "$P"

f="$P/$(cd "$P" && "$PY" -c 'import json;print(json.load(open("project.json"))["output"])')"
echo; echo "SMOKE TEST PASS: $f ($(du -h "$f" | cut -f1))"
echo "Review: $P/out/qc/contact_sheet.png and $P/out/stills/contact.png"
