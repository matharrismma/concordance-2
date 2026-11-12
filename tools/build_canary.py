#!/usr/bin/env python3
"""THE CANARY: the first build through the box build path (tools/box_build.py, run 2026-11-11-box-build).

    python tools/build_canary.py INPUTS OUTPUT ok     writes one fixed file, OUTPUT/canary.txt, and exits 0
    python tools/build_canary.py INPUTS OUTPUT fail   writes OUTPUT/canary-fail.txt, then exits 1: a failed build must
                                                     leave nothing behind, and this shows it on the box

It reads nothing and fetches nothing: tools/box_builds.txt gives it no inputs, so INPUTS is empty. It writes bytes,
never text, so its output is the same on Windows and on Linux and its hash is known before the box builds it.
Stdlib only, like every build tool.
"""
import os
import sys

CANARY = b"canary: built on the box by tools/box_build.py from tools/build_canary.py\n"
FAILED = b"canary-fail: written before a deliberate failure; no build directory may ever hold it\n"


def main(argv):
    if len(argv) != 3 or argv[2] not in ("ok", "fail"):
        print("usage: build_canary.py INPUTS OUTPUT ok|fail", file=sys.stderr)
        return 2
    inputs, out, mode = argv
    if os.listdir(inputs):
        print("the canary takes no inputs", file=sys.stderr)
        return 2
    name, body = ("canary.txt", CANARY) if mode == "ok" else ("canary-fail.txt", FAILED)
    with open(os.path.join(out, name), "wb") as fh:
        fh.write(body)
    if mode == "fail":
        print("canary-fail: exiting 1 on purpose", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
