#!/bin/sh
# THE BUILD PATH, the laptop's half (run 2026-11-11-box-build). tools/deploy.sh hands it
#
#   sh tools/deploy.sh --build <name> [--build <name> ...]
#   sh tools/deploy.sh --build-verify <name> [--build-verify <name> ...]
#
# with the box in BUILD_HOST, BUILD_KEY and BUILD_DEST, so no file but deploy.sh names it. A <name> is an entry of
# tools/box_builds.txt and nothing else: never a path, never a free argument. Everything is checked before any call.
#
# --build <name>: sends tools/box_builds.txt, tools/box_build.py and the entry's tool to their paths, and each of the
#   entry's inputs only into the unit's staging directory, data/builds/.inputs/<run id>/, at its repository path inside
#   it, never at its own repository path; starts tools/box_build.py on the box, detached, with a fresh run id, so it
#   finishes on its own; and polls for at most 45 minutes for data/builds/.results/<run id>.json, accepting only a
#   result that holds that run id. A build only ever adds data/builds/<name>/<content hash>/, which nothing serves until
#   an ordinary gated deploy ships a pin naming it, so whatever happens here (a failed build, a timeout, a dropped
#   session) nothing the site serves has changed.
# --build-verify <name>: takes the hash pinned for <name> in THIS laptop's src/concordance/build_pins.json, the file
#   about to be shipped, never the box's copy, and reads, by streaming this laptop's tools/box_build.py to the box's
#   python, that data/builds/<name>/<that hash>/ is there and re-hashes to its name. It writes nothing on the box.
#
# It calls ssh and scp and nothing else that reaches the box: no gate, no drift check, no child with box settings of
# its own. DEPLOY_NO_GATE is refused: a build never rides on an ungated deploy.
set -euf      # -f: no word here is ever a glob

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LISTING=tools/box_builds.txt
UNIT=tools/box_build.py
PINS=src/concordance/build_pins.json
NAME_RE='[a-z0-9][a-z0-9-]{0,62}'
SEG='[A-Za-z0-9_][A-Za-z0-9_.-]*'
# The rest of an entry after its name: the pattern tools/box_build.py's ENTRY_RE holds.
ENTRY_TAIL=' tools/[A-Za-z0-9_][A-Za-z0-9_-]*\.py [0-9a-f]{64} [0-9]{1,4}( in=[^ ]+)*( "[A-Za-z0-9._:=,+/@%-]*")*'
POLL_MAX=2700                                   # 45 minutes, the longest a poll waits
POLL_SECONDS=${BUILD_POLL_SECONDS:-$POLL_MAX}
POLL_INTERVAL=${BUILD_POLL_INTERVAL:-10}

refuse() { echo "build_ship: refused: $*" >&2; exit 2; }
one_line() { case "$1" in *'
'*) return 1 ;; esac; return 0; }

[ -z "${DEPLOY_NO_GATE:-}" ] || refuse "DEPLOY_NO_GATE is set: a build never rides on an ungated deploy"
[ -n "${BUILD_HOST:-}" ] && [ -n "${BUILD_KEY:-}" ] && [ -n "${BUILD_DEST:-}" ] \
    || refuse "the box is named only by tools/deploy.sh, which hands it here (sh tools/deploy.sh --build <name>)"
one_line "$BUILD_HOST$BUILD_KEY$BUILD_DEST" || refuse "the box's settings hold a newline"
case "$BUILD_DEST" in /*) ;; *) refuse "the destination is not an absolute path" ;; esac
printf '%s\n' "$BUILD_DEST" | grep -Eqx '[A-Za-z0-9_./-]+' || refuse "the destination holds a character this script will not quote"
for n in "$POLL_SECONDS" "$POLL_INTERVAL"; do
    case "$n" in ''|*[!0-9]*) refuse "BUILD_POLL_SECONDS and BUILD_POLL_INTERVAL are whole seconds" ;; esac
done
[ "$POLL_SECONDS" -le "$POLL_MAX" ] || refuse "a poll waits at most $POLL_MAX seconds"
[ "$#" -ge 2 ] || refuse "usage: sh tools/deploy.sh --build <listed name> [...] | --build-verify <listed name> [...]"

cd "$REPO"
[ -f "$LISTING" ] && [ -f "$UNIT" ] || refuse "$LISTING and $UNIT must both be here"

entry_of() {    # the one listing line of a name, carriage returns dropped (a Windows checkout writes CRLF)
    tr -d '\r' < "$LISTING" | grep -E "^$1 " || true
}
inputs_of() {   # the in= paths of an entry line, one per line
    for tok in $1; do case "$tok" in in=*) printf '%s\n' "${tok#in=}" ;; esac; done
}
pin_of() {      # the hash this laptop's pins file holds for a name, or nothing
    tr -d '\r' < "$PINS" | sed -n "s/^  \"$1\": \"\([0-9a-f]\{64\}\)\",\{0,1\}\$/\1/p"
}

# ---------------------------------------------------------------------------------- every check, before any call
jobs=""
while [ "$#" -gt 0 ]; do
    switch=$1
    case "$switch" in --build|--build-verify) ;; *) refuse "not a switch this path takes: $switch" ;; esac
    [ "$#" -ge 2 ] || refuse "$switch needs a listed name"
    name=$2
    shift 2
    one_line "$name" && printf '%s\n' "$name" | grep -Eqx "$NAME_RE" \
        || refuse "not a listed name (a name, never a path or a free argument): $name"
    entry=$(entry_of "$name")
    [ -n "$entry" ] || refuse "not a listed name: $name"
    [ "$(printf '%s\n' "$entry" | grep -c .)" -eq 1 ] || refuse "$name is listed more than once"
    printf '%s\n' "$entry" | grep -Eqx "$name$ENTRY_TAIL" || refuse "the entry for $name is not a well-formed listing line"
    tool=$(printf '%s\n' "$entry" | cut -d' ' -f2)
    [ -f "$tool" ] || refuse "$name's tool is not here: $tool"
    for p in $(inputs_of "$entry"); do
        case "$p" in /*) refuse "$name: an input is an absolute path: $p" ;; esac
        case "/$p/" in */./*|*/../*|*//*) refuse "$name: an input holds '.', '..' or an empty segment: $p" ;; esac
        case "$(printf '%s' "$p" | tr 'A-Z' 'a-z')" in data|data/*) refuse "$name: an input under data/ is refused: $p" ;; esac
        printf '%s\n' "$p" | grep -Eqx "$SEG(/$SEG)*" || refuse "$name: an input is not a plain repository path: $p"
        [ -f "$p" ] || refuse "$name: an input is not a file here: $p"
    done
    if [ "$switch" = --build-verify ]; then
        pin=$(pin_of "$name")
        [ -n "$pin" ] && [ "$(printf '%s\n' "$pin" | grep -c .)" -eq 1 ] || refuse "no single pin for $name in $PINS"
    fi
    jobs="$jobs $switch=$name"
done

LOCAL=$(mktemp -d)
trap 'rm -rf "$LOCAL"' EXIT
send() { scp -q -i "$BUILD_KEY" -o ConnectTimeout=10 "$1" "$BUILD_HOST:$BUILD_DEST/$2"; }

build() {
    name=$1
    entry=$(entry_of "$name")
    tool=$(printf '%s\n' "$entry" | cut -d' ' -f2)
    rid="$(date -u +%Y%m%dT%H%M%SZ)-$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')"
    printf '%s\n' "$rid" | grep -Eqx '[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}' || { echo "!! build $name: no run id could be made" >&2; return 1; }
    stage="data/builds/.inputs/$rid"
    echo "-- build $name: run $rid --"
    dirs=""
    for p in $(inputs_of "$entry"); do dirs="$dirs '$BUILD_DEST/$stage/$(dirname "$p")'"; done
    # Called as `build ... || exit 1`, so set -e does not reach in here: every call is checked by hand.
    if [ -n "$dirs" ]; then
        ssh -i "$BUILD_KEY" -o ConnectTimeout=10 "$BUILD_HOST" "mkdir -p$dirs" < /dev/null \
            || { echo "!! build $name: the staging directory could not be made" >&2; return 1; }
    fi
    for f in "$LISTING" "$UNIT" "$tool"; do
        send "$f" "$f" || { echo "!! build $name: $f could not be sent" >&2; return 1; }
    done
    for p in $(inputs_of "$entry"); do
        send "$p" "$stage/$p" || { echo "!! build $name: the input $p could not be staged" >&2; return 1; }
    done
    ssh -i "$BUILD_KEY" -o ConnectTimeout=10 "$BUILD_HOST" "cd '$BUILD_DEST' && nohup setsid nice -n 19 ionice -c 2 -n 7 .venv/bin/python -I $UNIT build --root '$BUILD_DEST' --run-id $rid $name < /dev/null > /dev/null 2>&1 &" < /dev/null \
        || { echo "!! build $name: the unit could not be started" >&2; return 1; }
    echo "   started on the box, detached; polling for data/builds/.results/$rid.json (at most ${POLL_SECONDS}s)"
    began=$(date +%s)
    got=""
    while :; do
        rm -f "$LOCAL/result.json"
        if scp -q -i "$BUILD_KEY" -o ConnectTimeout=10 "$BUILD_HOST:$BUILD_DEST/data/builds/.results/$rid.json" "$LOCAL/result.json" 2> /dev/null \
                && grep -Fq "\"run_id\": \"$rid\"" "$LOCAL/result.json" && grep -Fq "\"name\": \"$name\"" "$LOCAL/result.json"; then
            got=1
            break
        fi
        left=$(( POLL_SECONDS - ($(date +%s) - began) ))
        [ "$left" -gt 0 ] || break
        sleep $(( left < POLL_INTERVAL ? left : POLL_INTERVAL ))
    done
    if [ -z "$got" ]; then
        echo "!! build $name: no result for run $rid within ${POLL_SECONDS}s. Nothing the site serves has changed; a unit" >&2
        echo "   still running finishes on its own, and the next build removes what it leaves." >&2
        return 1
    fi
    tr -d '\r' < "$LOCAL/result.json" | sed 's/^/   /'
    if grep -Eq '^ "status": "(built|present)",?$' "$LOCAL/result.json"; then
        echo "-- build $name: done (run $rid) --"
        return 0
    fi
    echo "!! build $name failed (run $rid). Nothing the site serves has changed." >&2
    return 1
}

verify() {
    name=$1
    pin=$(pin_of "$name")
    echo "-- verify $name: data/builds/$name/$pin, the pin in this laptop's $PINS --"
    if tr -d '\r' < "$UNIT" | ssh -i "$BUILD_KEY" -o ConnectTimeout=10 "$BUILD_HOST" "cd '$BUILD_DEST' && .venv/bin/python -I - verify --root '$BUILD_DEST' $name $pin"; then
        echo "-- verified: data/builds/$name/$pin is on the box and re-hashes to its name --"
        return 0
    fi
    echo "!! data/builds/$name/$pin is not on the box as pinned: ship no pin for it" >&2
    return 1
}

for job in $jobs; do
    case "$job" in
        --build=*) build "${job#--build=}" || exit 1 ;;
        --build-verify=*) verify "${job#--build-verify=}" || exit 1 ;;
    esac
done
