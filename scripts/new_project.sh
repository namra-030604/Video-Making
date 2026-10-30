#!/usr/bin/env bash
# new_project.sh <folder> : scaffold a narrated video project from examples/hello-world (project.json + index.html).
# Then edit project.json "lines" (the script) and index.html (the scene), and run scripts/build.sh <folder>.
set -euo pipefail
PACK="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:?usage: new_project.sh <folder>}"
[ -e "$DEST/project.json" ] && { echo "$DEST/project.json already exists - not overwriting"; exit 1; }
mkdir -p "$DEST"/{audio,align,out,assets}
cp "$PACK/examples/hello-world/index.html" "$DEST/"
sed "s/\"name\": \"hello-world\"/\"name\": \"$(basename "$DEST")\"/; s#out/hello-world.mp4#out/$(basename "$DEST").mp4#" "$PACK/examples/hello-world/project.json" > "$DEST/project.json"
printf '# PROGRESS\n\nProject scaffolded from examples/hello-world.\n' > "$DEST/PROGRESS.md"
echo "scaffolded $DEST. Next: edit $DEST/project.json (lines, size) and $DEST/index.html, then: bash $PACK/scripts/build.sh $DEST"
