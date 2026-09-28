#!/usr/bin/env bash
# ONE SUPERVISED TRAINING TICK — run the loop a few BOUNDED steps, and if it LEARNED (bound new
# public-domain cards), SERVE them: restart the services staggered so the fruit is picked, never left
# hanging on the tree. Conservative and logged; PD-only-public via the proven pull_and_card path, with
# all its guards. Meant to be driven on a cadence by a supervisor who reads the output each tick.
#
#   sh tools/train_cadence.sh [steps]      # run from anywhere; default 2 steps
set -eu
cd "$(dirname "$0")/.."
STEPS="${1:-2}"

# give the run the ark + all service env (CONCORDANCE_SOURCES, etc.)
set -a; . ./.env; set +a
export CONCORDANCE_TRAINING=1

echo "== training tick: $STEPS step(s) =="
OUT="$(PYTHONPATH=src timeout 300 python3 tools/train_run.py "$STEPS" 2>&1 || true)"
echo "$OUT"

if echo "$OUT" | grep -q '"status": "learned"'; then
  echo "-- learned new cards -> SERVING (staggered restart), so no fruit is left hanging --"
  sudo systemctl restart nh-org; sleep 8
  sudo systemctl restart nh-com-2; sleep 8
  for i in $(seq 1 24); do
    a=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/health || echo 000)
    b=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/health || echo 000)
    if [ "$a" = "200" ] && [ "$b" = "200" ]; then echo "SERVED (healthy 8001=$a 8002=$b, poll $i)"; break; fi
    sleep 5
  done
else
  echo "-- nothing new learned this tick -> no restart needed (nothing hanging) --"
fi
