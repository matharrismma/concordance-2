#!/usr/bin/env bash
# Back up 2.0's generated data — the irreplaceable seals + ledger chain, plus the corpus and
# scripture/Strong's data. tar + sha256 -> $NH_BACKUP_DIR, keeping the last $NH_BACKUP_KEEP.
# Sovereign: tar + sha256sum only. Run daily (cron/timer) and before any risky migration.
#
#   CONCORDANCE_HOME   repo root        (default /home/nh/concordance-2)
#   NH_BACKUP_DIR      where tars land  (default /home/nh/backups)  -- on-box; see note below
#   NH_BACKUP_KEEP     how many to keep (default 14)
#
# NOTE: this writes to the SAME box by default (protects against bit-rot, a botched deploy, a
# bad migration — not a box loss). For true off-site, copy the tar elsewhere (e.g. the 12TB
# drive, object storage) — that destination is the operator's choice.
set -euo pipefail

ROOT="${CONCORDANCE_HOME:-/home/nh/concordance-2}"
DATA="$ROOT/data"
DEST="${NH_BACKUP_DIR:-/home/nh/backups}"
KEEP="${NH_BACKUP_KEEP:-14}"
TS="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$DEST"
ITEMS=()
for p in cas ledger activity.jsonl cards.jsonl bible_en.jsonl strongs; do
  [ -e "$DATA/$p" ] && ITEMS+=("$p")
done
if [ "${#ITEMS[@]}" -eq 0 ]; then
  echo "backup: nothing to back up in $DATA"; exit 0
fi

TAR="$DEST/nh-2.0-data-$TS.tar.gz"
tar czf "$TAR" -C "$DATA" "${ITEMS[@]}"
( cd "$DEST" && sha256sum "$(basename "$TAR")" > "$(basename "$TAR").sha256" )
echo "backup: $TAR ($(du -h "$TAR" | cut -f1)) — items: ${ITEMS[*]}"
cat "$TAR.sha256"

# Prune: keep the newest $KEEP
ls -1t "$DEST"/nh-2.0-data-*.tar.gz 2>/dev/null | tail -n +"$((KEEP + 1))" | while read -r old; do
  rm -f "$old" "$old.sha256"; echo "pruned $old"
done

echo "verify : sha256sum -c $TAR.sha256"
echo "restore: tar xzf $TAR -C <target-data-dir>  &&  python tools/integrity_check.py"
