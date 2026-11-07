#!/bin/sh
# The outside watch, installed on the box: the watch with its service and timer, and OOMPolicy=continue on each engine by a
# drop-in of its own beside the ones there, overwriting none. A gated ship path, named in docs/HARNESS.md: only the lead runs it.
#
# deploy/ is not on the box, so it runs from a folder of its own:
#
#   1. Copy these four files into one folder on the box that only root can write (root's own, mode 0700), with the LF
#      line ends the repository gives them:
#        install_watch.sh  nh-engine-watch  nh-engine-watch.service  nh-engine-watch.timer
#      It runs as root and installs what that folder holds, so a folder anyone else can write is a way into root.
#   2. sudo sh FOLDER/install_watch.sh
#   3. Read its last line, then remove the folder. The snapshot does not live in it.
#
#   sudo sh install_watch.sh --undo   puts back the newest snapshot, by hand. It needs only this script, so copy that back
#                                     (to a folder only root can write) if the folder has gone. Run again, it puts back
#                                     the snapshot before. After cells ship, mind what it takes away: the first snapshot
#                                     holds no OOMPolicy drop-in, so undoing to it takes OOMPolicy=continue off both
#                                     engines again, and a cell the kernel ends for memory would stop its unit.
#   sh install_watch.sh --root DIR    works under DIR in place of /, for a test with a stub systemctl.
#
# One install or undo runs at a time: a second is refused while the first holds the lock (flock, from util-linux).
#
# What it does, in order: takes the lock; refuses, touching nothing, a folder with a file missing, a carriage return or a
# watch that does not parse, and a drop-in of this name that it did not write; snapshots what it replaces, the timer's
# state, and each engine's main process and restart count; lays each file down whole; reloads systemd; enables and starts
# the timer; reads each back. All it ever asks of an engine is a read, so it restarts neither. Any failure after the
# snapshot puts the snapshot back, and reads that back too. An install cut short leaves its snapshot, for --undo.
#
# Its WATCH lines are safe for a public note: file names, process ids, restart counts. An error from a tool on stderr may
# name the folder, so that does not go in a note.
#
# Exit: 0 done and read back · 1 a read-back failed and the snapshot is back · 3 the snapshot could not be put back: it is
#       kept, and a human must look · 64 refused, nothing touched
set -u

SCRIPT=nh-engine-watch
SERVICE=nh-engine-watch.service
TIMER=nh-engine-watch.timer
DROPIN=30-oom-policy.conf
ENGINES="nh-engine nh-mcp"
BIN=usr/local/bin
UNITS=etc/systemd/system
ROOT= UNDO=

refuse() {
    echo "WATCH REFUSED: $1" >&2
    exit 64
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --undo) UNDO=1; shift ;;
        --root) [ "$#" -ge 2 ] || refuse "--root needs a directory"; ROOT=$2; shift 2 ;;
        *) refuse "unknown argument: $1" ;;
    esac
done
[ -n "$ROOT" ] || [ "$(id -u)" = 0 ] || refuse "run it with sudo"

# The lock is the kernel's, on this shell's descriptor 9, so it goes when the shell ends, however it ends: a run cut short
# leaves nothing to clear.
command -v flock >/dev/null || refuse "flock is not here"
command exec 9> "$ROOT/run/nh-engine-watch-install.lock" || refuse "the lock cannot be opened"
flock -n 9 || refuse "another install or undo is running"

SRC=$(dirname -- "$0")
SNAPSHOTS=$ROOT/var/lib/nh-engine-watch/snapshots
MANAGED="$BIN/$SCRIPT $UNITS/$SERVICE $UNITS/$TIMER"
for unit in $ENGINES; do
    MANAGED="$MANAGED $UNITS/$unit.service.d/$DROPIN"
done

dropin() {
    printf '%s\n' '# From deploy/install_watch.sh: a process the kernel ends for memory does not stop the unit.' \
        '[Service]' 'OOMPolicy=continue'
}

has_dropin() {
    dropin | cmp -s - "$1"
}

check_source() {
    for name in "$SCRIPT" "$SERVICE" "$TIMER"; do
        [ -f "$SRC/$name" ] || refuse "$name is not beside this script"
        tr -d '\r' < "$SRC/$name" | cmp -s - "$SRC/$name" || refuse "$name has carriage returns, and would break on the box"
    done
    sh -n "$SRC/$SCRIPT" || refuse "$SCRIPT does not parse"
    for unit in $ENGINES; do
        file=$ROOT/$UNITS/$unit.service.d/$DROPIN
        [ ! -e "$file" ] || has_dropin "$file" || refuse "$DROPIN on $unit is not this script's, and it overwrites none"
    done
}

read_engines() {
    for unit in $ENGINES; do
        echo "$unit $(systemctl show "$unit" -p MainPID --value) $(systemctl show "$unit" -p NRestarts --value)"
    done
}

newest() {
    last=$(ls "$SNAPSHOTS" 2>/dev/null | grep -E '^[0-9]+$' | sort -n | tail -n 1)
    [ -z "$last" ] || echo "$SNAPSHOTS/$last"
}

# Built under another name and moved into place whole, so --undo never reads half a snapshot. A file missing from it was
# not there before, and goes.
take_snapshot() {
    mkdir -p "$SNAPSHOTS" || return 1
    last=$(newest)
    last=${last##*/}
    next=$(( ${last:-0} + 1 ))
    work=$SNAPSHOTS/new.$$
    mkdir "$work" || return 1
    for rel in $MANAGED; do
        [ -e "$ROOT/$rel" ] || continue
        mkdir -p "$work/files/$(dirname "$rel")" && cp -p "$ROOT/$rel" "$work/files/$rel" || return 1
    done
    systemctl is-enabled "$TIMER" > "$work/timer-enabled" 2>/dev/null
    systemctl is-active "$TIMER" > "$work/timer-active" 2>/dev/null
    read_engines > "$work/engines" || return 1
    mv "$work" "$SNAPSHOTS/$next" || return 1
    snap=$SNAPSHOTS/$next
}

# Whole or not at all, so a timer firing now reads the old file or the new one.
put() {
    mkdir -p "$ROOT/$(dirname "$2")" && cp "$1" "$ROOT/$2.new" && chmod "$3" "$ROOT/$2.new" && mv -f "$ROOT/$2.new" "$ROOT/$2"
}

install_files() {
    dropin > "$snap/$DROPIN" || return 1
    put "$SRC/$SCRIPT" "$BIN/$SCRIPT" 755 || return 1
    put "$SRC/$SERVICE" "$UNITS/$SERVICE" 644 || return 1
    put "$SRC/$TIMER" "$UNITS/$TIMER" 644 || return 1
    for unit in $ENGINES; do
        put "$snap/$DROPIN" "$UNITS/$unit.service.d/$DROPIN" 644 || return 1
    done
}

check() {
    what=$1
    shift
    if "$@"; then
        echo "WATCH read back $what"
    else
        echo "WATCH FAILED $what"
        failed=1
    fi
}

read_back() {
    failed=0
    check "$SCRIPT" cmp -s "$SRC/$SCRIPT" "$ROOT/$BIN/$SCRIPT"
    check "$SCRIPT can run" test -x "$ROOT/$BIN/$SCRIPT"
    check "$SERVICE" cmp -s "$SRC/$SERVICE" "$ROOT/$UNITS/$SERVICE"
    check "$TIMER" cmp -s "$SRC/$TIMER" "$ROOT/$UNITS/$TIMER"
    for unit in $ENGINES; do
        check "$DROPIN on $unit" has_dropin "$ROOT/$UNITS/$unit.service.d/$DROPIN"
        check "OOMPolicy of $unit" test "$(systemctl show "$unit" -p OOMPolicy --value)" = continue
    done
    check "$TIMER enabled" test "$(systemctl is-enabled "$TIMER" 2>/dev/null)" = enabled
    check "$TIMER active" test "$(systemctl is-active "$TIMER" 2>/dev/null)" = active
    engines=$(read_engines)
    check "engines unmoved: $(echo $engines)" test "$engines" = "$(cat "$snap/engines")"
    [ "$failed" = 0 ]
}

# The timer goes back to the state the snapshot read. A timer that was off is turned off while its file is still there.
restore() {
    enabled=$(cat "$snap/timer-enabled")
    active=$(cat "$snap/timer-active")
    [ "$active" = active ] || systemctl stop "$TIMER" 2>/dev/null
    [ "$enabled" = enabled ] || systemctl disable "$TIMER" 2>/dev/null
    for rel in $MANAGED; do
        if [ -e "$snap/files/$rel" ]; then
            cp -p "$snap/files/$rel" "$ROOT/$rel.new" && mv -f "$ROOT/$rel.new" "$ROOT/$rel"
        else
            rm -f "$ROOT/$rel" "$ROOT/$rel.new"
        fi
    done
    systemctl daemon-reload
    reloaded=$?
    [ "$enabled" != enabled ] || systemctl enable "$TIMER"
    [ "$active" != active ] || systemctl start "$TIMER"
    failed=0
    for rel in $MANAGED; do
        if [ -e "$snap/files/$rel" ]; then
            check "$rel as it was" cmp -s "$snap/files/$rel" "$ROOT/$rel"
        else
            check "$rel gone" test ! -e "$ROOT/$rel"
        fi
    done
    check "the reload" test "$reloaded" = 0
    check "$TIMER as it was" test "$(systemctl is-enabled "$TIMER" 2>/dev/null) $(systemctl is-active "$TIMER" 2>/dev/null)" = "$enabled $active"
    [ "$failed" = 0 ]
}

# A snapshot put back is spent, so --undo after it reaches the one before. One that could not be is kept for a human.
put_back() {
    if restore; then
        rm -rf "$snap"
        echo "WATCH $1"
        exit "$2"
    fi
    echo "WATCH RESTORE FAILED: the snapshot is kept, and a human must look"
    exit 3
}

if [ -n "$UNDO" ]; then
    snap=$(newest)
    [ -n "$snap" ] || refuse "no snapshot to put back"
    put_back undone 0
fi

check_source
take_snapshot || { rm -rf "$SNAPSHOTS/new.$$"; refuse "the snapshot could not be taken"; }
if install_files && systemctl daemon-reload && systemctl enable --now "$TIMER"; then
    if read_back; then
        echo "WATCH installed"
        exit 0
    fi
else
    echo "WATCH FAILED the install"
fi
put_back restored 1
