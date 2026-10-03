#!/usr/bin/env bash
# HETZNER IS PRIMARY (Matt, 2026-10-03: "Hetzner was always meant to be primary"). The box is the trunk; the
# first off-box copy is a Hetzner Storage Box in the same datacenter, filled from the box at wire speed by
# rsync over ssh (port 23), nightly, after the box's own backup. Everything else — the 12 TB ark on the
# desktop, a USB stick — pulls from the trunk at its own pace. A known branch: one named host, one key that
# lives only on the box, and a checksum pass after every push ("a copy that arrives unverified is not a copy").
#
# INERT until configured. It reads /home/nh/.config/nh/storagebox.env:
#     STORAGEBOX_USER=u123456            # the Storage Box's username (also its hostname prefix)
#     STORAGEBOX_HOST=u123456.your-storagebox.de
#     STORAGEBOX_PORT=23                 # Hetzner's ssh/rsync port for Storage Boxes
#     STORAGEBOX_PATH=/narrowhighway     # a directory on the box (created on first run)
# and the key /home/nh/.ssh/id_ed25519_storagebox (generated 2026-10-03; the public half, in RFC4716 form,
# must be added to the Storage Box's authorized keys in the Hetzner Robot panel or via `ssh-copy-id -p 23`).
#
# What it keeps on the Storage Box (the whole keeping, re-creatable from here alone):
#     backups/      the nightly data tars + .sha256 (tools/backup.sh), the memory seals, the substrate tars
#     shards/       data/shards (the frozen freight: the shelves' full bodies, 1.9 GB) — rsync deltas
#     acquisitions/ data/acquisitions (the stored source archives)
#     releases/     /srv/nh-releases — the field pack + the weekly Kiwix ZIM (served at /releases/)
# Run by nh-storagebox.timer (03:40, after backup.sh at 03:00). Logs to /home/nh/backups/storagebox.log.
set -u
ENV="${NH_STORAGEBOX_ENV:-/home/nh/.config/nh/storagebox.env}"
KEY="${NH_STORAGEBOX_KEY:-/home/nh/.ssh/id_ed25519_storagebox}"
LOG="${NH_STORAGEBOX_LOG:-/home/nh/backups/storagebox.log}"
ROOT="${NH_ROOT:-/home/nh/concordance-2}"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
if [ ! -f "$ENV" ]; then
    say "not configured: $ENV absent (order the Storage Box, add the key, write the env file) — nothing to do"
    exit 0
fi
# shellcheck disable=SC1090
. "$ENV"
: "${STORAGEBOX_USER:?}" "${STORAGEBOX_HOST:?}"
PORT="${STORAGEBOX_PORT:-23}"
DEST="${STORAGEBOX_PATH:-/narrowhighway}"
[ -f "$KEY" ] || { say "FAILED: key $KEY missing"; exit 1; }
SSH="ssh -i $KEY -p $PORT -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new"
R="$STORAGEBOX_USER@$STORAGEBOX_HOST"
# the Storage Box has no shell; directories are made through sftp
printf 'mkdir %s\nmkdir %s/backups\nmkdir %s/shards\nmkdir %s/acquisitions\nmkdir %s/releases\nbye\n' \
    "$DEST" "$DEST" "$DEST" "$DEST" "$DEST" | sftp -q -i "$KEY" -P "$PORT" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$R" >/dev/null 2>&1 || true
push() {  # push <local dir> <remote subdir> [extra rsync args...]
    local src="$1" sub="$2"; shift 2
    [ -d "$src" ] || { say "skip $sub: $src absent"; return 0; }
    if rsync -az --delete --partial --timeout=120 "$@" -e "$SSH" "$src/" "$R:$DEST/$sub/" >>"$LOG" 2>&1; then
        # the checksum pass: a dry run that compares whole-file checksums must find nothing left to send
        local left
        left="$(rsync -nac --out-format='%n' "$@" -e "$SSH" "$src/" "$R:$DEST/$sub/" 2>>"$LOG" | grep -vcE '^(\./)?$' || true)"
        if [ "${left:-0}" = "0" ]; then say "verified $sub ($(du -sm "$src" | cut -f1) MB)"; else say "WARNING: $sub — $left files differ after push"; return 1; fi
    else
        say "FAILED: rsync $sub (see $LOG)"; return 1
    fi
}
ok=0
push /home/nh/backups backups --include='*.tar.gz' --include='*.sha256' --include='*.log' --exclude='*' || ok=1
push "$ROOT/data/shards" shards || ok=1
push "$ROOT/data/acquisitions" acquisitions || ok=1
push /srv/nh-releases releases || ok=1     # the public releases root (served at narrowhighway.com/releases/)
if [ "$ok" = 0 ]; then say "storage box in step with the trunk"; else say "storage box: one or more pushes failed"; fi
exit $ok
