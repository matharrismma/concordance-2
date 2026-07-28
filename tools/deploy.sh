#!/bin/sh
# Deploy files to the droplet and restart the services — the whole ritual, codified.
#
#   sh tools/deploy.sh src/concordance/web/api.py site/ask.html [...]
#
# What it does, in order:
#   1. One tar-over-ssh transfer (single connection; preserves repo-relative paths) — replaces
#      the old one-scp-per-file ritual and its per-file handshakes.
#   2. STAGGERED restart: witness (nh-org) first, health-polled back to 200, THEN secular
#      (nh-com-2). Both services hold the corpus in RAM and reload it on restart; restarting
#      them together doubles the CPU spike and overlaps their downtime. Staggering keeps one
#      face of the site up at every moment.
#   3. Patient health polling, built in. The port binds only after the corpus loads (up to
#      ~30s), and the first probe after a restart often fails transiently (curl exit 7 /
#      status 000) even when all is well — a lesson learned the slow way, encoded here so it
#      never has to be re-learned. A failed first poll is NOT a failed deploy; the poll
#      retries until the service answers or the timeout is real.
#
# What it deliberately does NOT do: git anything. Commit and push remain explicit, separate,
# human-reviewed actions (docs: git discipline — never add -A, stage exact paths).
set -eu

HOST="nh@5.78.186.55"
KEY="$HOME/.ssh/id_ed25519_nh"
DEST="/home/nh/concordance-2"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

[ "$#" -ge 1 ] || { echo "usage: sh tools/deploy.sh <repo-relative file> [...]"; exit 2; }

cd "$REPO"
for f in "$@"; do
    [ -f "$f" ] || { echo "not a file (paths are repo-relative): $f"; exit 2; }
done

echo "-- transferring $# file(s) in one connection --"
tar -cf - "$@" | ssh -i "$KEY" -o ConnectTimeout=10 "$HOST" "tar -xf - -C $DEST"

poll() {  # poll <port> <label> — patient: transient 000s right after restart are normal
    i=0
    while [ "$i" -lt 30 ]; do
        code=$(ssh -i "$KEY" -o ConnectTimeout=10 "$HOST" \
            "curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://127.0.0.1:$1/health" 2>/dev/null || echo 000)
        if [ "$code" = "200" ]; then echo "   $2 up (after $((i*3))s)"; return 0; fi
        i=$((i+1)); sleep 3
    done
    echo "   $2 did NOT come back within 90s (last: $code)"; return 1
}

echo "-- restarting witness (nh-org, :8001) --"
ssh -i "$KEY" -o ConnectTimeout=10 "$HOST" "sudo systemctl restart nh-org"
poll 8001 "witness"

echo "-- restarting secular (nh-com-2, :8002) --"
ssh -i "$KEY" -o ConnectTimeout=10 "$HOST" "sudo systemctl restart nh-com-2"
poll 8002 "secular"

echo "-- deployed: $* --"
