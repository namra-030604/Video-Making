#!/usr/bin/env bash
# new_project.sh <folder> [--vertical] : scaffold a motion-studio project (index.html + mslib.js + beats.json + project.json)
set -euo pipefail
SK="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:?usage: new_project.sh <folder> [--vertical]}"
mkdir -p "$DEST"/{assets,audio,out}
cp -n "$SK/templates/index.html" "$SK/templates/mslib.js" "$SK/templates/beats.json" "$DEST/"
W=1920; H=1080
if [ "${2:-}" = "--vertical" ]; then
  W=1080; H=1920
  sed -i 's/const W = 1920, H = 1080;/const W = 1080, H = 1920;/' "$DEST/index.html"
  sed -i 's/"size": \[1920, 1080\]/"size": [1080, 1920]/' "$DEST/beats.json"
  echo "NOTE: vertical 1080x1920 set; the starter layout coordinates are for 16:9, re-lay them out."
fi
[ -f "$DEST/project.json" ] || cat > "$DEST/project.json" <<JSON
{ "name": "$(basename "$DEST")", "width": $W, "height": $H, "fps": 60, "duration": 3.0, "page": "index.html",
  "render": { "part_frames": 120, "crf": 18, "threads": 2, "hash_dirs": ["assets"] },
  "audio": { "lufs": -14, "true_peak": -1.5 }, "qc": { "freeze_s": 0.75 }, "output": "out/$(basename "$DEST").mp4" }
JSON
[ -f "$DEST/CHANGELOG.md" ] || printf '# Changelog\n\n## V1\n- first render\n' > "$DEST/CHANGELOG.md"
echo "scaffolded $DEST  (edit beats.json first, then index.html; keep project.json duration = beats.json duration)"
