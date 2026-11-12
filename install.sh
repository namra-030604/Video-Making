#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
elif command -v uv >/dev/null 2>&1; then exec uv run --no-project --python 3.13 python "$HERE/vsp.py" "$@"
else echo "Python 3.8+ or uv is needed to bootstrap. Install Python or uv first." >&2; exit 1; fi
exec "$PY" "$HERE/vsp.py" "$@"
