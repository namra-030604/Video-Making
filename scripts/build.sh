#!/usr/bin/env bash
# build.sh <project-dir> [--force] : the whole pipeline, one heavy step at a time, restart-safe.
#   voice -> word alignment -> music/SFX + loudness -> review stills -> parts render -> subtitle QC -> final QC
# Every step skips itself when its inputs have not changed, so re-running after a crash continues where it stopped.
set -euo pipefail
PACK="$(cd "$(dirname "$0")/.." && pwd)"
P="$(cd "${1:?usage: build.sh <project-dir> [--force]}" && pwd)"; F="${2:-}"
PY="$(cat "$PACK/.vsp-state/python" 2>/dev/null || echo python3)"
export VSP_CACHE="${VSP_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/video-skill-pack}" TORCH_HOME="${TORCH_HOME:-${VSP_CACHE:-$HOME/.cache/video-skill-pack}/torch}"
echo "== memory before starting"; free -h | sed -n '1,2p'
step() { echo; echo "== $1"; shift; "$@"; }
step "1/7 voice (Kokoro, speed 1.0)"   "$PY" "$PACK/scripts/make_voice.py"  --project "$P" $F
step "2/7 align words (MMS_FA)"        "$PY" "$PACK/scripts/align_words.py" --project "$P" $F
step "3/7 music + SFX + loudness"      "$PY" "$PACK/scripts/make_audio.py"  --project "$P" $F
step "4/7 review stills"               node "$PACK/scripts/stills.mjs" --project "$P" --scan
step "5/7 render (verified parts)"     node "$PACK/scripts/render.mjs" --project "$P"
step "6/7 subtitle QC"                 node "$PACK/scripts/subtitle_qc.mjs" --project "$P"
step "7/7 final QC"                    "$PY" "$PACK/scripts/qc_final.py" --project "$P"
