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

# ---------------------------------------------------------------------------------------------
# THE FALLBACK. Matt, 2026-08-02: "Make sure we have fallback procedures in place for all actions."
#
# Until now this script overwrote files in place with no copy of what it replaced. The staggered
# restart below is a real canary — the witness is polled back to 200 BEFORE the secular service is
# touched, so a bad deploy stops at half the fleet — but there was no way to put the old bytes
# back. Recovery depended on a human remembering to re-deploy from git, at the exact moment the
# site was down and they were least calm.
#
# So: snapshot first, revert automatically if a health check fails. Two cases, both handled —
# files that EXISTED are restored from the tar, files that are NEW are deleted, because restoring
# a file that was never there is impossible and leaving it is not a revert.
# ---------------------------------------------------------------------------------------------
TS="$(date -u +%Y%m%dT%H%M%SZ)"
ROLLBACK="/home/nh/deploy-rollback"
SNAP="$ROLLBACK/$TS"

echo "-- snapshotting the current state of $# file(s) -> $SNAP --"
ssh -i "$KEY" -o ConnectTimeout=10 "$HOST" "
set -eu
mkdir -p '$SNAP'
cd '$DEST'
: > '$SNAP/added.txt'
present=''
for f in $*; do
    if [ -f \"\$f\" ]; then present=\"\$present \$f\"; else echo \"\$f\" >> '$SNAP/added.txt'; fi
done
if [ -n \"\$present\" ]; then tar -cf '$SNAP/prev.tar' \$present; fi
echo \"   snapshot: \$(echo \$present | wc -w) existing, \$(wc -l < '$SNAP/added.txt') new\"
# Keep the last 10 snapshots; a rollback older than that is a git checkout, not a revert.
ls -1dt '$ROLLBACK'/*/ 2>/dev/null | tail -n +11 | xargs -r rm -rf
"

revert() {
    echo "!! HEALTH CHECK FAILED — reverting to the pre-deploy state ($TS)"
    ssh -i "$KEY" -o ConnectTimeout=10 "$HOST" "
set -eu
cd '$DEST'
[ -f '$SNAP/prev.tar' ] && tar -xf '$SNAP/prev.tar' -C '$DEST' || true
while IFS= read -r f; do
    [ -n \"\$f\" ] && rm -f '$DEST'/\"\$f\"
done < '$SNAP/added.txt'
sudo systemctl restart nh-org
sudo systemctl restart nh-com-2
" || echo "   !! the revert itself failed — go in by hand: $SNAP holds prev.tar + added.txt"
    echo "-- reverted. re-checking both doors --"
    poll 8001 "witness (reverted)" || echo "   !! STILL DOWN after revert — manual intervention needed"
    poll 8002 "secular (reverted)" || echo "   !! STILL DOWN after revert — manual intervention needed"
    echo "-- the deploy was undone. Nothing was lost: $SNAP holds what was replaced. --"
}

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

# The witness is the CANARY: it restarts first and must answer 200 before the secular service is
# touched at all. If it does not come back, we revert and stop — the secular half is still serving
# the old code and has never been restarted, so readers on .com never saw the bad deploy.
echo "-- restarting witness (nh-org, :8001) --"
ssh -i "$KEY" -o ConnectTimeout=10 "$HOST" "sudo systemctl restart nh-org"
poll 8001 "witness" || { revert; exit 1; }

echo "-- restarting secular (nh-com-2, :8002) --"
ssh -i "$KEY" -o ConnectTimeout=10 "$HOST" "sudo systemctl restart nh-com-2"
poll 8002 "secular" || { revert; exit 1; }

echo "-- deployed: $* --"

# 4. PROVE the box matches the repo, module for module. The deploy target is not a checkout:
#    corpus_db.py was absent from it for days under a green gate, and airlock.py was found
#    missing the first time this guard ran. A deploy that ends on hope is how that happens.
#    Advisory (never fails the deploy — the files you just sent are already there); it prints
#    the drift so it cannot hide.
python "$REPO/tools/verify_deploy.py" --soft || true
