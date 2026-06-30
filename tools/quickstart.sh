#!/usr/bin/env bash
# Quickstart — stand up your own Narrow Highway engine in one command.
#
# Creates a virtualenv, installs the engine + the symbolic-math moat, runs the self-check
# (58/58, 0 false-positives), and serves it on http://127.0.0.1:8000. Sovereign + offline:
# nothing phones home. Verify / seal / the keep work immediately; add the corpus + Scripture
# data later for search + the witness surface (see docs/SELF_HOST.md).
#
#   bash tools/quickstart.sh            # secular surface on :8000
#   PORT=8001 SURFACE=witness bash tools/quickstart.sh
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
PORT="${PORT:-8000}"
SURFACE="${SURFACE:-secular}"

echo "1/3  virtualenv (.venv)…"
[ -d .venv ] || "$PY" -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate

echo "2/3  install (engine + math moat)…"
pip install -q --upgrade pip
pip install -q -e ".[math]"

echo "3/3  self-check (the moat must be 58/58, 0 false-positives)…"
python tools/benchmark.py | tail -2

cat <<MSG

  ✓ ready — serving the $SURFACE surface on http://127.0.0.1:$PORT  (Ctrl-C to stop)

  try it:
    curl -s -X POST http://127.0.0.1:$PORT/verify -H content-type:application/json \\
      -d '{"mode":"equality","params":{"expr_a":"2+2","expr_b":"4","variables":{}}}'

  the keep (operator window):  set CONCORDANCE_KEEP_TOKEN, then /keep.html?token=…
  add the library + Scripture:  see docs/SELF_HOST.md

MSG
exec python -m concordance serve --surface "$SURFACE" --port "$PORT"
