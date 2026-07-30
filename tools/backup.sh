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
KEEP="${NH_BACKUP_KEEP:-7}"   # the tar is ~30x larger now; 7 days of the WHOLE keeping
TS="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$DEST"

# 2026-07-29 — WIDENED, because the old list was a false comfort. It named six items
# (cas ledger activity.jsonl cards.jsonl bible_en.jsonl strongs) and produced an 18 MB tar,
# while the data directory held 1.9 GB: every ACQUISITION — source_cards 227M, gutenberg 116M,
# scripture_cards 52M, taxonomy 38M, ISBE, OEIS, the minted edges — was backed up NOWHERE.
# (The weekly "full" on this box belongs to Lighthouse 1.0 and covers none of it.) A green
# backup log meant the receipts were safe and the library was not.
#
# Now: the WHOLE data directory, minus what is derived and rebuildable —
#   shards/       rebuilt from the jsonl by tools/build_corpus_db.py (~2 min)
#   acquisitions/ upstream archives, re-fetchable from their public sources
#   *.tmp/*.part  work in progress
#   *.bak         pre-change snapshots of a file that is already backed up here in full. Seven of
#                 them (232 MB of cards.jsonl copies) were riding along in EVERY nightly tarball,
#                 so the same history was paid for again each night. Archived once to the ark
#                 (verified 8/8 by sha256, 2026-07-30) and removed from the box; excluded here so
#                 a future .bak cannot quietly start refilling the backups.
ITEMS=()
while IFS= read -r p; do ITEMS+=("$p"); done < <(
  cd "$DATA" && ls -A | grep -vE '^(shards|acquisitions)$' | grep -vE '\.(tmp|part|bak)$'
)
if [ "${#ITEMS[@]}" -eq 0 ]; then
  echo "backup: nothing to back up in $DATA"; exit 0
fi

TAR="$DEST/nh-2.0-data-$TS.tar.gz"
tar czf "$TAR" -C "$DATA" "${ITEMS[@]}"
( cd "$DEST" && sha256sum "$(basename "$TAR")" > "$(basename "$TAR").sha256" )
echo "backup: $TAR ($(du -h "$TAR" | cut -f1)) — ${#ITEMS[@]} items"
cat "$TAR.sha256"

# Prune: keep the newest $KEEP
ls -1t "$DEST"/nh-2.0-data-*.tar.gz 2>/dev/null | tail -n +"$((KEEP + 1))" | while read -r old; do
  rm -f "$old" "$old.sha256"; echo "pruned $old"
done

echo "verify : sha256sum -c $TAR.sha256"
echo "restore: tar xzf $TAR -C <target-data-dir>  &&  python tools/integrity_check.py"
