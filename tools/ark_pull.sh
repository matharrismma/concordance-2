#!/usr/bin/env bash
# THE ARK — pull the newest backups off the Hetzner box onto the 12 TB drive, and VERIFY them.
#
# 2026-07-29. Until tonight every backup lived on the box it backed up: 2.7 GB of tarballs on
# the same droplet, so losing the droplet lost the backups too. Matt named the hardware — a
# Hetzner server, a 12 TB drive, and this device — which is exactly the three-tier ark:
#
#   Hetzner  the serving node        (works, and backs itself up hourly/daily)
#   12 TB    the ark                 (offsite durability; this script feeds it)
#   device   the working node        (the repo, the shard builder, the gate)
#
# Pulls the newest data tarball + its .sha256, then RE-HASHES the local copy and compares. A
# copy that arrives corrupt is worse than no copy, because it looks like safety.
#
#   ARK_DIR   where it lands (default /d/NarrowHighway-Backups/hetzner)
#   NH_KEY    ssh key        (default ~/.ssh/id_ed25519_nh)
#
#   sh tools/ark_pull.sh          # newest data tarball
#   sh tools/ark_pull.sh shards   # also mirror the shards — the whole keeping, self-contained
set -eu

HOST="${NH_HOST:-nh@5.78.186.55}"
KEY="${NH_KEY:-$HOME/.ssh/id_ed25519_nh}"
ARK="${ARK_DIR:-/d/NarrowHighway-Backups/hetzner}"
REMOTE_BACKUPS="/home/nh/backups"

mkdir -p "$ARK"

newest="$(ssh -i "$KEY" -o ConnectTimeout=10 "$HOST" "ls -1t $REMOTE_BACKUPS/nh-2.0-data-*.tar.gz | head -1")"
[ -n "$newest" ] || { echo "no data tarball found on the box"; exit 1; }
base="$(basename "$newest")"
echo "-- newest on the box: $base"

if [ -f "$ARK/$base" ]; then
    echo "   already on the ark; verifying the copy that is there"
else
    echo "-- pulling to $ARK --"
    scp -i "$KEY" -o ConnectTimeout=10 "$HOST:$newest" "$ARK/$base"
    scp -i "$KEY" -o ConnectTimeout=10 "$HOST:$newest.sha256" "$ARK/$base.sha256" 2>/dev/null || true
fi

# VERIFY: re-hash what actually landed and compare to what the box signed.
want="$(cut -d' ' -f1 < "$ARK/$base.sha256" 2>/dev/null || true)"
got="$(sha256sum "$ARK/$base" | cut -d' ' -f1)"
if [ -z "$want" ]; then
    echo "!! no .sha256 alongside — the copy cannot be verified (recorded, not hidden)"
    exit 1
elif [ "$want" = "$got" ]; then
    echo "   VERIFIED  $got"
    echo "   $(du -h "$ARK/$base" | cut -f1) on the ark"
else
    echo "!! HASH MISMATCH — the copy is not the record"
    echo "   box:  $want"
    echo "   ark:  $got"
    exit 1
fi

# The SOURCE archives (CrossWire modules, upstream zips). Excluded from the box's daily tar as
# "re-fetchable", which is true only while the upstream still exists — so the ark keeps them.
# That is what an ark is for: the things that are hard to get again.
echo "-- mirroring the source archives --"
mkdir -p "$ARK/acquisitions"
scp -i "$KEY" -o ConnectTimeout=10 "$HOST:/home/nh/concordance-2/data/acquisitions/*" "$ARK/acquisitions/" 2>/dev/null   || echo "   (none on the box yet — they live on this device)"
for f in data/acquisitions/*; do
    [ -e "$f" ] || continue
    b="$(basename "$f")"
    [ -f "$ARK/acquisitions/$b" ] || { cp "$f" "$ARK/acquisitions/$b"; echo "   + $b (from this device)"; }
done
echo "   $(ls -1 "$ARK/acquisitions" 2>/dev/null | wc -l) source archive(s) on the ark"

if [ "${1:-}" = "shards" ]; then
    echo "-- mirroring the shards (the whole keeping, self-contained) --"
    mkdir -p "$ARK/shards"
    scp -i "$KEY" -o ConnectTimeout=10 "$HOST:/home/nh/concordance-2/data/shards/*" "$ARK/shards/"
    echo "   $(ls -1 "$ARK/shards" | wc -l) files on the ark"
fi

# Retention: the ark is 12 TB and a data tarball is ~130 MB — keep a long tail (a year of
# dailies is ~47 GB, which is 0.4% of the drive). Depth is the point of an ark.
KEEP="${ARK_KEEP:-90}"
ls -1t "$ARK"/nh-2.0-data-*.tar.gz 2>/dev/null | tail -n +"$((KEEP + 1))" | while read -r old; do
    rm -f "$old" "$old.sha256"; echo "   pruned $(basename "$old") (keeping $KEEP)"
done

echo "-- the ark holds $(ls -1 "$ARK"/nh-2.0-data-*.tar.gz 2>/dev/null | wc -l) verified backup(s) --"
