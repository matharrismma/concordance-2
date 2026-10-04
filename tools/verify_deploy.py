#!/usr/bin/env python3
"""Prove the box matches the repo — the guard that was missing when corpus_db.py went absent.

GAPS.md G6. The droplet receives files by scp, not by checkout, so a module nothing had yet
imported was simply never there — for days, under a green gate, because the gate runs against
the REPO. The suite is guarded that way already (`tests/MANIFEST.txt`); the source was not.

WIDENED 2026-10-02 (Fable review). The first version proved `src/concordance/**/*.py` only and
printed "the box matches the repo, file for file" — while 29 test files were stale and 39 were
missing on the box, 8 tools stale and 37 missing, and conductor/ absent. The suite run on the box
then reported 18 red files of which 11 were simply old tests. A parity proof scoped to one
directory teaches you that the box matches when it does not. Two scopes now:

    HARD  src/ tests/ tools/ conductor/ site/ + README.md HANDOFF.md pyproject.toml
          — what the servers and the suite READ. Drift here is a verdict (exit 1 unless --soft).
    SOFT  every other tracked file (docs/, eval/, deploy/, data/ spines, .github/ …)
          — counted, listed with --all, never fails the deploy. deploy/Caddyfile and the unit
          files are the box's live truth by design; data spines are rebuilt from, not served.

The comparison is git's own: the repo side is the blob id of HEAD (`git ls-tree`), the box side
is the blob id recomputed from the file's bytes with CRLF normalised (the working copy is
Windows, the box is POSIX; comparing raw bytes marks every text file DIFFERENT and teaches you
to ignore the check). Reports, per scope:

    MISSING      in the repo, absent on the box      (the corpus_db.py failure, caught)
    DIFFERENT    present on both, contents differ    (a stale deploy)
    EXTRA        on the box under a HARD dir, not tracked here — reported, NEVER deleted
                 (a retired generator still on the box poisoned test_privacy; an operator's
                 own script on the box is not ours to remove)

Read-only over ssh; it changes nothing.

    sh tools/deploy.sh <files>          # calls this at the end (--soft)
    python tools/verify_deploy.py       # exit 1 on HARD drift
    python tools/verify_deploy.py --all # list SOFT drift too
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # a cp1252 console must not garble the report
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parent.parent
HOST = "nh@5.78.186.55"
KEY = str(Path.home() / ".ssh" / "id_ed25519_nh")
DEST = "/home/nh/concordance-2"

HARD_DIRS = ("src/", "tests/", "tools/", "conductor/", "site/")
HARD_FILES = ("README.md", "HANDOFF.md", "pyproject.toml")

# BOX-OWNED: tracked files that a process ON THE BOX rewrites in place, so the box's copy is the
# live truth and the repo's is the seed (2026-10-03: the hive's theorymap step writes
# site/theories.html every turn; the deploy then reported it DIFFERENT — a true report of a
# designed state, which teaches the reader to ignore DIFFERENT). Reported under their own heading,
# never a drift verdict; MISSING still is (absent is absent). Name the writer, so a reader can check.
BOX_OWNED = {
    "site/theories.html": "nh-hive theorymap (tools/hive_cycle.py), daily 10:00 UTC",
}

# Runs on the box. Reads "<blob> <path>" lines on stdin, recomputes each path's git blob id from
# its bytes with CR stripped, and lists untracked files under the HARD dirs. Pure stdlib.
_REMOTE = r'''
import hashlib, os, sys
hard = %r
want = {}
for line in sys.stdin:
    line = line.rstrip("\r\n")   # text-mode subprocess on Windows feeds CRLF; a CR-tailed path matches nothing
    if not line: continue
    sha, path = line.split(" ", 1); want[path] = sha
for path, sha in want.items():
    if not os.path.isfile(path): print("M", path); continue
    data = open(path, "rb").read()
    if b"\0" not in data[:8000]:          # git's own text heuristic: never normalise a binary (fonts, onnx)
        data = data.replace(b"\r\n", b"\n")
    h = hashlib.sha1(b"blob %%d\0" %% len(data) + data).hexdigest()
    if h != sha: print("D", path)
for d in hard:
    for dp, dns, fns in os.walk(d.rstrip("/")):
        dns[:] = [x for x in dns if x != "__pycache__"]
        for fn in fns:
            p = os.path.join(dp, fn).replace(os.sep, "/")
            if p not in want and not fn.endswith((".pyc", ".pyo")): print("E", p)
'''


def _is_hard(path: str) -> bool:
    return path.startswith(HARD_DIRS) or path in HARD_FILES


def _tracked() -> dict:
    r = subprocess.run(["git", "ls-tree", "-r", "HEAD", "--format=%(objectname) %(path)"],
                       cwd=ROOT, capture_output=True, text=True, check=True)
    out = {}
    for line in r.stdout.splitlines():
        sha, path = line.split(" ", 1)
        out[path] = sha
    return out


def _remote(tracked: dict):
    script = _REMOTE % (HARD_DIRS,)
    cmd = f"cd {DEST} && python3 -c {_sq(script)}"
    feed = "".join(f"{sha} {path}\n" for path, sha in tracked.items())
    r = subprocess.run(["ssh", "-i", KEY, "-o", "ConnectTimeout=10", HOST, cmd],
                       input=feed, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"could not reach the box: {r.stderr.strip()[:200]}")
        return None
    missing, diff, extra = [], [], []
    for line in r.stdout.splitlines():
        kind, _, path = line.partition(" ")
        {"M": missing, "D": diff, "E": extra}.get(kind, []).append(path)
    return sorted(missing), sorted(diff), sorted(extra)


def _sq(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"


def _report(label: str, items: list, limit: int) -> None:
    if not items:
        return
    print(f"  {label}: {len(items)}")
    for f in items[:limit]:
        print(f"    {f}")
    if len(items) > limit:
        print(f"    … and {len(items) - limit} more")


def main() -> int:
    soft = "--soft" in sys.argv
    show_all = "--all" in sys.argv
    tracked = _tracked()
    res = _remote(tracked)
    if res is None:
        print("SKIPPED — the box could not be reached (this is a fact about the network, "
              "not a verdict on the deploy).")
        return 0 if soft else 1
    missing, diff, extra = res
    hard_missing = [p for p in missing if _is_hard(p)]
    hard_diff = [p for p in diff if _is_hard(p) and p not in BOX_OWNED]
    box_owned = [f"{p}  <- {BOX_OWNED[p]}" for p in diff if p in BOX_OWNED]
    soft_missing = [p for p in missing if not _is_hard(p)]
    soft_diff = [p for p in diff if not _is_hard(p)]
    n_hard = sum(1 for p in tracked if _is_hard(p))
    print(f"HARD scope (src tests tools conductor site + root files) — {n_hard} tracked")
    _report("MISSING on the box", hard_missing, 12)
    _report("DIFFERENT", hard_diff, 12)
    _report("BOX-OWNED (rewritten on the box by design; the box is the live truth)", box_owned, 12)
    _report("EXTRA on the box (untracked here; reported, never deleted)", extra, 8)
    hard_ok = not (hard_missing or hard_diff)
    if hard_ok:
        print("  the box matches the repo, file for file, in everything the servers and the suite read.")
    print(f"SOFT scope (docs eval deploy data .github …) — {len(tracked) - n_hard} tracked: "
          f"{len(soft_missing)} missing, {len(soft_diff)} different on the box"
          + ("" if show_all else "  (--all to list)"))
    if show_all:
        _report("missing", soft_missing, 200)
        _report("different", soft_diff, 200)
    if hard_ok:
        return 0
    print("\nDRIFT in the HARD scope — deploy the named files, or delete them on the box if they are gone here.")
    return 0 if soft else 1


if __name__ == "__main__":
    sys.exit(main())
