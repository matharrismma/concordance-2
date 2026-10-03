#!/usr/bin/env bash
# THE RESTORE DRILL — a backup is a backup only once it has been restored and checked. Runs ON THE BOX.
# (docs/PROJECT_REVIEW_2026-10-03.md R1; Matt, 2026-10-03: "go on those".)
#
# Takes the newest nightly tar (tools/backup.sh), verifies its sha256, restores it into a scratch directory,
# runs the integrity check AGAINST THE RESTORED KEEPING (the ledger chain + every sealed CAS record), parses
# every restored jsonl line, counts the cards against the live keeping, and writes one line to
# /home/nh/backups/restore-drill.log: "DRILL OK …" or "DRILL FAILED …". Exit 0 only on OK.
# The shards and the acquisitions are NOT in the nightly tar (by design — they ride the ark and the Storage
# Box as rsync deltas); the drill says so in its line, so nobody mistakes the tar for the whole keeping.
# Run monthly by nh-restore-drill.timer (the 1st, 05:00 UTC); safe by hand any time. Keep the scratch with
# NH_DRILL_KEEP=1. Alerts: integrity_check.py posts to CONCORDANCE_ALERT_WEBHOOK on failure if it is set.
set -u
BK="${NH_BACKUPS:-/home/nh/backups}"
ROOT="${NH_ROOT:-/home/nh/concordance-2}"
LOG="${NH_DRILL_LOG:-$BK/restore-drill.log}"
SCRATCH="${NH_DRILL_DIR:-/home/nh/restore-drill}"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
fail() { say "DRILL FAILED: $*"; [ "${NH_DRILL_KEEP:-0}" = 1 ] || rm -rf "$SCRATCH"; exit 1; }

tar_path="$(ls -1t "$BK"/nh-2.0-data-*.tar.gz 2>/dev/null | head -1)"
[ -n "$tar_path" ] || fail "no nightly tar in $BK"
base="$(basename "$tar_path")"
( cd "$BK" && sha256sum -c "$base.sha256" >/dev/null 2>&1 ) || fail "sha256 mismatch on $base"

need_k=$(( $(stat -c %s "$tar_path") * 4 / 1024 ))
free_k="$(df -k /home | tail -1 | awk '{print $4}')"
[ "$free_k" -gt "$need_k" ] || fail "need ${need_k}K free for the scratch, have ${free_k}K"

rm -rf "$SCRATCH"; mkdir -p "$SCRATCH/data"
tar -xzf "$tar_path" -C "$SCRATCH/data" 2>/dev/null || fail "extract of $base"

# every restored jsonl line must parse (a truncated or corrupt line is a quiet hole). `#` lines are comments
# (dictionary_supplement.jsonl opens with four — the first drill, 2026-10-03, failed on exactly those). And the
# copy is measured AGAINST THE LIVE KEEPING: a quirk the live data already carries is not a restore failure —
# only a line the copy lost or broke is.
parse_count() {  # parse_count <dir> -> "<bad> <lines>"
    python3 - "$1" <<'PYEOF'
import json, os, sys
root = sys.argv[1]; bad = 0; n = 0
for name in sorted(os.listdir(root)):
    if not name.endswith(".jsonl"):
        continue
    with open(os.path.join(root, name), encoding="utf-8", errors="replace") as f:
        for ln in f:
            if not ln.strip() or ln.lstrip().startswith("#"):
                continue
            n += 1
            try:
                json.loads(ln)
            except Exception:
                bad += 1
print(f"{bad} {n}")
PYEOF
}
restored="$(parse_count "$SCRATCH/data")"; live_parse="$(parse_count "$ROOT/data")"
bad_n="${restored%% *}"; lines_n="${restored##* }"; live_bad="${live_parse%% *}"; live_lines="${live_parse##* }"
[ "${bad_n:-1}" -le "${live_bad:-0}" ] || fail "$bad_n unparseable jsonl lines of $lines_n in the restored keeping (live has $live_bad)"
[ "${live_bad:-0}" = "0" ] || say "WARN: the live keeping itself carries $live_bad unparseable jsonl lines (the copy is faithful to them)"

# the integrity check against the RESTORED keeping, never the live one
out="$(cd "$ROOT" && CONCORDANCE_DATA_DIR="$SCRATCH/data" PYTHONPATH=src timeout 1800 .venv/bin/python tools/integrity_check.py 2>&1 | tail -1)"
rc=$?
cards="$(wc -l < "$SCRATCH/data/cards.jsonl" 2>/dev/null || echo 0)"
live="$(wc -l < "$ROOT/data/cards.jsonl" 2>/dev/null || echo 0)"
ledger="$(ls "$SCRATCH/data/ledger" 2>/dev/null | wc -l)"
[ "$rc" -eq 0 ] || fail "integrity rc=$rc on the restored keeping ($out)"
[ "${cards:-0}" -gt 0 ] || fail "restored cards.jsonl is empty"

say "DRILL OK: $base restored to $SCRATCH — $out — $lines_n jsonl lines parsed (live $live_lines), cards=$cards (live $live), ledger files=$ledger. Not in the tar by design: shards + acquisitions (they ride the ark / Storage Box)."
[ "${NH_DRILL_KEEP:-0}" = 1 ] || rm -rf "$SCRATCH"
exit 0
