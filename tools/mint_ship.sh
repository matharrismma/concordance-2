#!/bin/sh
# THE MINT PATH, the laptop's half (run 2026-11-13-stick-ship). tools/deploy.sh hands it
#
#   sh tools/deploy.sh --mint-check <name> && sh tools/deploy.sh --mint <name>
#   sh tools/deploy.sh --mint-retract <name>
#
# (each switch repeatable) with the box in MINT_HOST, MINT_KEY and MINT_DEST, so no file but deploy.sh names it. A
# <name> is an entry of tools/stick_mints.txt and nothing else: never a path, never a free argument. Before any call it
# checks, for every switch: the name is listed once and its line is well formed; tools/stick_mints.txt,
# tools/stick_mint.py and data/sticks/<name>.json are tracked and equal to HEAD, and HEAD is contained in origin's
# default branch as this laptop's remote-tracking ref records it, so only reviewed, pushed bytes are ever sent or
# compared; this laptop's data/sticks/<name>.json, carriage returns removed, hashes (sha256sum) to the listed hash; and
# --mint-retract is never given a canary (a line marked expect=present or expect=refused).
#
# Then every switch reads, by streaming this laptop's tools/stick_mint.py to the box's python (its entry-check uses the
# standard library alone), that the box's data/sticks/<name>.json hashes to the same listed hash, and refuses before
# anything is sent or started otherwise. The entry reaches the box only by an ordinary gated deploy, never by this path.
# --mint-check <name>: stops there; it writes nothing.
# --mint <name> and --mint-retract <name>: send tools/stick_mints.txt and tools/stick_mint.py to their paths, start the
#   unit on the box, detached, with a fresh run id, so it finishes on its own, and poll for at most 15 minutes for
#   data/mints/.results/<run id>.json, accepting only a result that holds that run id and that name. A timeout or a
#   failed result exits non-zero and says so.
#
# It calls ssh, scp, git and sha256sum and nothing else that reaches the box or the repository: no gate, no drift check,
# no child with box settings of its own. DEPLOY_NO_GATE is refused: a mint never rides on an ungated deploy.
set -euf      # -f: no word here is ever a glob

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LISTING=tools/stick_mints.txt
UNIT=tools/stick_mint.py
NAME_RE='[a-z0-9][a-z0-9_]{0,62}'
# The rest of a listing line after its name: the pattern tools/stick_mint.py's LINE_RE holds.
LINE_TAIL=' [0-9a-f]{64}( [A-Za-z0-9_().-]{1,80}=[0-9a-f]{64})*( expect=(present|refused))?'
POLL_MAX=900                                    # 15 minutes, the longest a poll waits
POLL_SECONDS=${MINT_POLL_SECONDS:-$POLL_MAX}
POLL_INTERVAL=${MINT_POLL_INTERVAL:-10}

refuse() { echo "mint_ship: refused: $*" >&2; exit 2; }
one_line() { case "$1" in *'
'*) return 1 ;; esac; return 0; }

[ -z "${DEPLOY_NO_GATE:-}" ] || refuse "DEPLOY_NO_GATE is set: a mint never rides on an ungated deploy"
[ -n "${MINT_HOST:-}" ] && [ -n "${MINT_KEY:-}" ] && [ -n "${MINT_DEST:-}" ] \
    || refuse "the box is named only by tools/deploy.sh, which hands it here (sh tools/deploy.sh --mint <name>)"
one_line "$MINT_HOST$MINT_KEY$MINT_DEST" || refuse "the box's settings hold a newline"
case "$MINT_DEST" in /*) ;; *) refuse "the destination is not an absolute path" ;; esac
printf '%s\n' "$MINT_DEST" | grep -Eqx '[A-Za-z0-9_./-]+' || refuse "the destination holds a character this script will not quote"
for n in "$POLL_SECONDS" "$POLL_INTERVAL"; do
    case "$n" in ''|*[!0-9]*) refuse "MINT_POLL_SECONDS and MINT_POLL_INTERVAL are whole seconds" ;; esac
done
[ "$POLL_SECONDS" -le "$POLL_MAX" ] || refuse "a poll waits at most $POLL_MAX seconds"
[ "$POLL_INTERVAL" -ge 1 ] || refuse "MINT_POLL_INTERVAL is at least one second"
[ "$#" -ge 2 ] || refuse "usage: sh tools/deploy.sh --mint-check <listed name> && sh tools/deploy.sh --mint <listed name> | --mint-retract <listed name>"

cd "$REPO"
[ -f "$LISTING" ] && [ -f "$UNIT" ] || refuse "$LISTING and $UNIT must both be here"

entry_of() {    # the one listing line of a name, carriage returns dropped (a Windows checkout writes CRLF)
    tr -d '\r' < "$LISTING" | grep -E "^$1 " || true
}
committed() {   # every path given is tracked and equal to HEAD
    git ls-files --error-unmatch -- "$@" > /dev/null 2>&1 && git diff --quiet HEAD -- "$@"
}

# ---------------------------------------------------------------------------------- every check, before any call
jobs=""
while [ "$#" -gt 0 ]; do
    switch=$1
    case "$switch" in --mint|--mint-check|--mint-retract) ;; *) refuse "not a switch this path takes: $switch" ;; esac
    [ "$#" -ge 2 ] || refuse "$switch needs a listed name"
    name=$2
    shift 2
    one_line "$name" && printf '%s\n' "$name" | grep -Eqx "$NAME_RE" \
        || refuse "not a listed name (a name, never a path or a free argument): $name"
    entry=$(entry_of "$name")
    [ -n "$entry" ] || refuse "not a listed name: $name"
    [ "$(printf '%s\n' "$entry" | grep -c .)" -eq 1 ] || refuse "$name is listed more than once"
    printf '%s\n' "$entry" | grep -Eqx "$name$LINE_TAIL" || refuse "the line for $name is not a well-formed listing line"
    if [ "$switch" = --mint-retract ]; then
        case " $entry " in *' expect='*) refuse "$name is a canary: a line marked expect=present or expect=refused is never retracted" ;; esac
    fi
    committed "$LISTING" "$UNIT" || refuse "$LISTING and $UNIT must be tracked and equal to HEAD: commit and push them first"
    committed "data/sticks/$name.json" || refuse "data/sticks/$name.json must be tracked and equal to HEAD: commit and push it first"
    listed=$(printf '%s\n' "$entry" | cut -d' ' -f2)
    here=$(tr -d '\r' < "data/sticks/$name.json" | sha256sum | cut -d' ' -f1)
    [ "$here" = "$listed" ] || refuse "this laptop's data/sticks/$name.json hashes to $here, not to the listed $listed"
    jobs="$jobs $switch=$name"
done
default=$(git symbolic-ref -q --short refs/remotes/origin/HEAD) \
    || refuse "this laptop records no default branch for origin (git remote set-head origin --auto)"
git merge-base --is-ancestor HEAD "$default" \
    || refuse "HEAD is not contained in $default as this laptop records it: push it first, then fetch"

LOCAL=$(mktemp -d)
trap 'rm -rf "$LOCAL"' EXIT
listed_hash() { entry_of "$1" | cut -d' ' -f2; }

# ---------------------------------------------------------------------------------- the box's copy of each entry
for job in $jobs; do
    name=${job#*=}
    listed=$(listed_hash "$name")
    echo "-- check $name: the box's data/sticks/$name.json against the listed $listed --"
    if ! tr -d '\r' < "$UNIT" | ssh -i "$MINT_KEY" -o ConnectTimeout=10 "$MINT_HOST" "cd '$MINT_DEST' && .venv/bin/python -I -B - entry-check --root '$MINT_DEST' $name $listed"; then
        echo "mint_ship: refused: the box's data/sticks/$name.json is not the listed entry; ship it first by an ordinary deploy. Nothing was sent or started." >&2
        exit 2
    fi
done

mint() {
    switch=$1 name=$2
    verb=mint
    [ "$switch" = --mint-retract ] && verb=retract
    rid="$(date -u +%Y%m%dT%H%M%SZ)-$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')"
    printf '%s\n' "$rid" | grep -Eqx '[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}' || { echo "!! $verb $name: no run id could be made" >&2; return 1; }
    echo "-- $verb $name: run $rid --"
    # Called as `mint ... || exit 1`, so set -e does not reach in here: every call is checked by hand.
    for f in "$LISTING" "$UNIT"; do
        scp -q -i "$MINT_KEY" -o ConnectTimeout=10 "$f" "$MINT_HOST:$MINT_DEST/$f" || { echo "!! $verb $name: $f could not be sent" >&2; return 1; }
    done
    ssh -i "$MINT_KEY" -o ConnectTimeout=10 "$MINT_HOST" "cd '$MINT_DEST' && nohup setsid nice -n 19 ionice -c 2 -n 7 .venv/bin/python -I -B $UNIT $verb $name --root '$MINT_DEST' --run-id $rid < /dev/null > /dev/null 2>&1 &" < /dev/null \
        || { echo "!! $verb $name: the unit could not be started" >&2; return 1; }
    echo "   started on the box, detached; polling for data/mints/.results/$rid.json (at most ${POLL_SECONDS}s)"
    began=$(date +%s)
    got=""
    while :; do
        rm -f "$LOCAL/result.json"
        if scp -q -i "$MINT_KEY" -o ConnectTimeout=10 "$MINT_HOST:$MINT_DEST/data/mints/.results/$rid.json" "$LOCAL/result.json" 2> /dev/null \
                && tr -d '\r' < "$LOCAL/result.json" | grep -Eqx " \"run_id\": \"$rid\",?" \
                && tr -d '\r' < "$LOCAL/result.json" | grep -Eqx " \"name\": \"$name\",?"; then
            got=1
            break
        fi
        left=$(( POLL_SECONDS - ($(date +%s) - began) ))
        [ "$left" -gt 0 ] || break
        sleep $(( left < POLL_INTERVAL ? left : POLL_INTERVAL ))
    done
    if [ -z "$got" ]; then
        echo "!! $verb $name: no result for run $rid within ${POLL_SECONDS}s. A unit still running finishes on its own;" >&2
        echo "   read data/mints/.results/$rid.json before another mint." >&2
        return 1
    fi
    tr -d '\r' < "$LOCAL/result.json" | sed 's/^/   /'
    ok='minted|present'
    [ "$verb" = retract ] && ok='retracted|absent'
    if tr -d '\r' < "$LOCAL/result.json" | grep -Eqx " \"status\": \"($ok)\",?"; then
        echo "-- $verb $name: done (run $rid) --"
        return 0
    fi
    echo "!! $verb $name did not succeed (run $rid): read its status and reason above." >&2
    return 1
}

for job in $jobs; do
    case "$job" in
        --mint-check=*) echo "-- checked: ${job#--mint-check=} on the box is the listed entry; nothing was sent or started --" ;;
        --mint=*) mint --mint "${job#--mint=}" || exit 1 ;;
        --mint-retract=*) mint --mint-retract "${job#--mint-retract=}" || exit 1 ;;
    esac
done
