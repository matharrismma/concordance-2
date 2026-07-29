#!/usr/bin/env python3
"""Prove the box matches the repo — the guard that was missing when corpus_db.py went absent.

GAPS.md G6. The droplet receives files by scp, not by checkout, so a module nothing had yet
imported was simply never there — for days, under a green gate, because the gate runs against
the REPO. The suite is guarded that way already (`tests/MANIFEST.txt`); the source was not.

This hashes every `src/concordance/**/*.py` here, asks the box to hash its own, and reports:

    MISSING      in the repo, absent on the box      (the corpus_db.py failure, caught)
    DIFFERENT    present on both, contents differ    (a stale deploy)
    EXTRA        on the box, not in the repo         (a file deleted here but never there)

Read-only over ssh; it changes nothing. Exit 1 on any drift so `deploy.sh` can end on proof
rather than on hope.

    sh tools/deploy.sh <files>          # calls this at the end
    python tools/verify_deploy.py       # or run it any time
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "nh@5.78.186.55"
KEY = str(Path.home() / ".ssh" / "id_ed25519_nh")
DEST = "/home/nh/concordance-2"


def _local():
    out = {}
    base = ROOT / "src" / "concordance"
    for p in sorted(base.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        rel = p.relative_to(ROOT).as_posix()
        # normalise line endings: the working copy is Windows (CRLF), the box is POSIX (LF).
        # Comparing raw bytes would report every file as DIFFERENT and teach us to ignore it.
        data = p.read_bytes().replace(b"\r\n", b"\n")
        out[rel] = hashlib.sha256(data).hexdigest()[:16]
    return out


def _remote():
    # Normalise line endings on the BOX too. The working copy is Windows (CRLF) and the box
    # receives those bytes verbatim, so hashing raw bytes on one side and normalised bytes on
    # the other marks every file DIFFERENT — a check that cries wolf teaches you to ignore it.
    cmd = (f"cd {DEST} && find src/concordance -name '*.py' -not -path '*__pycache__*' "
           f"-exec sh -c 'printf \"%s  %s\\n\" \"$(tr -d \"\\r\" < \"$1\" | sha256sum | cut -d\" \" -f1)\" \"$1\"' _ {{}} \\;")
    r = subprocess.run(["ssh", "-i", KEY, "-o", "ConnectTimeout=10", HOST, cmd],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"could not reach the box: {r.stderr.strip()[:200]}")
        return None
    out = {}
    for line in r.stdout.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            out[parts[1].strip()] = parts[0][:16]
    return out


def main() -> int:
    local = _local()
    remote = _remote()
    if remote is None:
        print("SKIPPED — the box could not be reached (this is a fact about the network, "
              "not a verdict on the deploy).")
        return 0 if "--soft" in sys.argv else 1
    missing = sorted(set(local) - set(remote))
    extra = sorted(set(remote) - set(local))
    diff = sorted(f for f in set(local) & set(remote) if local[f] != remote[f])
    print(f"src modules — repo {len(local)} · box {len(remote)}")
    for label, items in (("MISSING on the box", missing), ("DIFFERENT", diff),
                         ("EXTRA on the box", extra)):
        if items:
            print(f"  {label}: {len(items)}")
            for f in items[:12]:
                print(f"    {f}")
            if len(items) > 12:
                print(f"    … and {len(items) - 12} more")
    if not (missing or diff or extra):
        print("  the box matches the repo, file for file.")
        return 0
    print("\nDRIFT — deploy the named files, or delete them on the box if they are gone here.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
