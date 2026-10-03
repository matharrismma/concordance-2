#!/usr/bin/env bash
# THE DECISION MEMORY, SEALED — tar + sha256 of the agent's decision memory (Matt's words, dated, verbatim)
# onto the 12 TB ark and the box. The written continuity of every decision is one of the three things
# that compound (docs/PROJECT_REVIEW_2026-10-03.md, R2: bus factor 1). Run daily by the Windows task
# "NarrowHighway Memory Seal"; safe to run by hand any time. Known branches only: this drive, this box.
set -eu
MEM="${NH_MEMORY_DIR:-$HOME/.claude/projects/C--Users-hdven-OneDrive-Desktop/memory}"
ARK="${NH_ARK_MEMORY:-/d/NarrowHighway-Backups/memory}"
HOST="${NH_HOST:-nh@5.78.186.55}"
KEY="${NH_KEY:-$HOME/.ssh/id_ed25519_nh}"
KEEP="${NH_MEMORY_KEEP:-14}"
LOG="$ARK/seal.log"
mkdir -p "$ARK"
ts="$(date +%Y%m%d)"
name="memory-$ts.tar.gz"
[ -d "$MEM" ] || { echo "$(date -u +%FT%TZ) FAILED: no memory dir at $MEM" | tee -a "$LOG"; exit 1; }
tar -czf "$ARK/$name" -C "$(dirname "$MEM")" "$(basename "$MEM")"
( cd "$ARK" && sha256sum "$name" > "$name.sha256" && sha256sum -c "$name.sha256" >/dev/null )
n="$(tar -tzf "$ARK/$name" | grep -c '\.md$' || true)"
echo "$(date -u +%FT%TZ) sealed: $name ($n files, $(du -k "$ARK/$name" | cut -f1) KB) on the ark" | tee -a "$LOG"
# the second branch: the box (verified on arrival; a copy that arrives unverified is not a copy)
if scp -q -i "$KEY" -o ConnectTimeout=15 -o BatchMode=yes "$ARK/$name" "$ARK/$name.sha256" "$HOST:/home/nh/backups/" \
   && ssh -i "$KEY" -o ConnectTimeout=15 -o BatchMode=yes "$HOST" "cd /home/nh/backups && sha256sum -c '$name.sha256' >/dev/null"; then
    echo "$(date -u +%FT%TZ) box copy verified: $name" | tee -a "$LOG"
else
    echo "$(date -u +%FT%TZ) WARNING: box copy not verified (ark copy is good)" | tee -a "$LOG"
fi
# rotation: keep the last $KEEP seals on the ark (the box rotates its own)
ls -1t "$ARK"/memory-*.tar.gz 2>/dev/null | tail -n +$((KEEP + 1)) | while read -r old; do rm -f "$old" "$old.sha256"; done
