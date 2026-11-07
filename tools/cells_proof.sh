#!/bin/sh
# The forkserver path, proved on Linux: only the cell test files, on the step's bytes, beside the engines and touching
# nothing they use. tests/test_cells.py runs on spawn at the harness gate; its Linux cases run here.
#
#   sh cells_proof.sh --tree TAR --paths FILE --python PY --base DIR [--limit SECONDS] [--memory SIZE]
#
#   --tree    a tar of the whole tree: the step's base with the step's paths laid over, each path's bytes as the checkout
#             holds them. diff_hash reads bytes, so a tree packed by another route can print another hash.
#   --paths   the step's path list, one per line, as its gate event names them.
#   --python  the Python that has pytest and the math extra.
#   --base    where the private directory goes. Outside /tmp, since the unit may run with a /tmp of its own.
#
# What it does, in order: reads each engine's MainPID and NRestarts; makes a private directory and unpacks the tree in it;
# prints harness.diff_hash from the unpacked tree over the path list, before any test, so the hash is of the bytes that
# run (no git: diff_hash needs none when it is given the paths); runs the tests by systemd-run under the engine's own
# hardening, at nice 19, with a time limit, a memory limit and no network of its own, as the engine's user; removes the
# directory and reads back that it is gone; reads each engine again. It runs only on the owner's word, and it is no ship.
#
# Everything it prints is safe for a public note: the private directory, the tree and the Python are named by placeholder.
#
# Exit: 0 all green and nothing moved · 1 the tests were red · 2 an engine moved · 3 the directory is still there · 64 usage
set -eu

UNIT=nh-engine
ENGINES="nh-engine nh-mcp"
TESTS=tests/test_cells.py
HARDENING="NoNewPrivileges PrivateTmp PrivateDevices ProtectSystem ProtectHome ProtectKernelTunables ProtectKernelModules
           ProtectKernelLogs ProtectControlGroups ProtectClock ProtectHostname RestrictRealtime RestrictSUIDSGID
           LockPersonality MemoryDenyWriteExecute"
TREE= PATHS= PYTHON= BASE= LIMIT=1800 MEMORY=3G

while [ "$#" -gt 0 ]; do
    case "$1" in
        --tree) TREE=$2 ;;
        --paths) PATHS=$2 ;;
        --python) PYTHON=$2 ;;
        --base) BASE=$2 ;;
        --limit) LIMIT=$2 ;;
        --memory) MEMORY=$2 ;;
        *) echo "unknown argument: $1" >&2; exit 64 ;;
    esac
    shift 2
done
if [ -z "$TREE" ] || [ -z "$PATHS" ] || [ -z "$PYTHON" ] || [ -z "$BASE" ]; then
    echo "usage: sh cells_proof.sh --tree TAR --paths FILE --python PY --base DIR [--limit SECONDS] [--memory SIZE]" >&2
    exit 64
fi
[ -f "$TREE" ] && [ -f "$PATHS" ] && [ -d "$BASE" ] || { echo "no such tree, path list or base" >&2; exit 64; }

read_engines() {
    for unit in $ENGINES; do
        printf '%s %s %s\n' "$unit" "$(systemctl show -p MainPID --value "$unit")" "$(systemctl show -p NRestarts --value "$unit")"
    done
}

BEFORE=$(read_engines)
RUN_AS=$(systemctl show -p User --value "$UNIT")
DIR=$(mktemp -d "$BASE/cells-proof.XXXXXX")     # 0700 by mktemp's own rule
OUT=$(mktemp "$BASE/cells-proof-out.XXXXXX")    # outside the directory, which the engine's user owns while the tests run
remove() {
    sudo rm -rf "$DIR"
    rm -f "$OUT"
}
trap remove EXIT
trap 'exit 1' INT TERM

mkdir "$DIR/tree" "$DIR/tmp"
tar -xf - -C "$DIR/tree" < "$TREE"              # by stdin, so no path reads as a remote host

HASH=$("$PYTHON" -c '
import sys
tree, listing = sys.argv[1:3]
sys.path.insert(0, tree + "/tools")
import harness
with open(listing, encoding="utf-8") as fh:
    print(harness.diff_hash(tree, "", [line.strip() for line in fh if line.strip()]))
' "$DIR/tree" "$PATHS")
echo "PROOF diff_hash $HASH"
echo "PROOF python $("$PYTHON" --version 2>&1)"

sudo chown -R "$RUN_AS" "$DIR"
set -- --wait --pipe --collect --quiet --uid="$RUN_AS" --working-directory="$DIR/tree" \
    -p Nice=19 -p RuntimeMaxSec="$LIMIT" -p MemoryMax="$MEMORY" -p OOMScoreAdjust=1000 -p PrivateNetwork=yes \
    -p ReadWritePaths="$DIR" \
    -E PYTHONPATH="$DIR/tree/src:$DIR/tree/tools" -E CONCORDANCE_DATA_DIR="$DIR/tree/data" \
    -E CONCORDANCE_STRONGS_DIR="$DIR/tree/data/strongs" -E TMPDIR="$DIR/tmp" -E HOME="$DIR/tmp"
for name in $HARDENING; do
    value=$(systemctl show -p "$name" --value "$UNIT")
    if [ -n "$value" ]; then
        set -- "$@" -p "$name=$value"
    fi
done
set -- "$@" -- "$PYTHON" -m pytest -p no:cacheprovider --color=no --tb=short -v -rs $TESTS

RED=0
sudo systemd-run "$@" > "$OUT" 2>&1 || RED=1
sed -e "s|$DIR|<private>|g" -e "s|$PYTHON|<python>|g" -e 's|^rootdir: .*|rootdir: <tree>|' "$OUT"

trap - EXIT
remove
if [ -e "$DIR" ]; then
    echo "PROOF THE DIRECTORY IS STILL THERE"
    exit 3
fi
echo "PROOF removed"

AFTER=$(read_engines)
if [ "$BEFORE" != "$AFTER" ]; then
    echo "PROOF AN ENGINE MOVED"
    printf 'before\n%s\nafter\n%s\n' "$BEFORE" "$AFTER"
    exit 2
fi
echo "PROOF engines unchanged"
printf '%s\n' "$AFTER"
if [ "$RED" -ne 0 ]; then
    echo "PROOF RED"
    exit 1
fi
echo "PROOF green"
