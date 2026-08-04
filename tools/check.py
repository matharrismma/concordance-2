#!/usr/bin/env python3
"""The regression gate, runnable now — the moat + the full suite + the coverage floor.

Same checks CI runs, in one command, so the gate doesn't depend on a remote being wired:

    python tools/check.py

Exits non-zero on ANY failure (a false-positive in the moat, a failing test, or
integrity-core coverage below the floor). Sovereign: if coverage/pytest aren't installed it
falls back to running each test file as a script, so the moat + suite still gate.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
CORE = "*/cas.py,*/ledger.py,*/record.py,*/signing.py,*/validate.py,*/receipts.py,*/derivation.py"
FLOOR = "90"  # raised from 75 (Matt, 2026-07-28: "all aspects above 90%") — the trust kernel's
              # honesty paths are now tested as behavior in tests/test_trust_kernel_edges.py


def _run(cmd: list) -> int:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    return subprocess.call(cmd, cwd=ROOT, env=ENV)


def _has(mod: str) -> bool:
    return subprocess.call([sys.executable, "-c", f"import {mod}"], env=ENV,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def _suite_is_whole() -> int:
    """A gate that runs whatever happens to be on disk reports PASS on a suite with holes.

    The deploy target is not a git checkout — tests arrive by scp — so 21 of 72 files (the
    moat-guard isolation test, the crisis invariant, the gate tests) were simply absent there
    and never ran, for months, under a green GATE PASS. MANIFEST lists what the suite IS;
    a missing file now fails the gate instead of quietly shrinking it.
    """
    man = os.path.join(ROOT, "tests", "MANIFEST.txt")
    if not os.path.exists(man):
        print("\nMISSING tests/MANIFEST.txt — cannot prove the suite is whole", flush=True)
        return 1
    with open(man, encoding="utf-8") as fh:
        want = {ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")}
    have = {os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "tests", "test_*.py"))}
    missing, extra = sorted(want - have), sorted(have - want)
    print(f"\n$ suite integrity: {len(have)}/{len(want)} test files present", flush=True)
    for m in missing:
        print(f"  MISSING (never ran): {m}", flush=True)
    for e in extra:
        print(f"  UNLISTED (add to tests/MANIFEST.txt): {e}", flush=True)
    return 1 if (missing or extra) else 0


# THE GATE RUNS ALONE — a lock, because resolve failed three times in one night.
#
# 2026-08-01: a heavy job was started beside a running gate three separate times. Each time the
# suite slowed from ~14 minutes to 50+, and each time the SAME wire test (test_no_stale_reads)
# failed on a 30-second localhost timeout — a false failure costing a full re-run to disprove.
# The test is right; it measures the wire. The DISCIPLINE was what kept breaking, so it stops
# being a discipline and becomes a mechanism.
_LOCK = os.path.join(ROOT, ".gate.lock")


def _take_the_floor() -> bool:
    """True if we hold the floor. A stale lock (dead pid) is reclaimed, said out loud."""
    if os.path.exists(_LOCK):
        try:
            with open(_LOCK, encoding="utf-8") as fh:
                pid = int((fh.read().split() or ["0"])[0])
        except (OSError, ValueError):
            pid = 0
        alive = False
        if pid:
            try:
                os.kill(pid, 0)                     # signal 0: does that process exist?
                alive = True
            except OSError:
                alive = False
        if alive:
            print(f"ANOTHER HEAVY JOB HOLDS THE FLOOR (pid {pid}). The gate runs alone — "
                  f"contention has produced three false failures. Wait, or remove {_LOCK} "
                  f"if you know it is dead.", flush=True)
            return False
        print(f"(reclaiming a stale lock from pid {pid or '?'})", flush=True)
    with open(_LOCK, "w", encoding="utf-8") as fh:
        fh.write(str(os.getpid()) + " check.py\n")
    return True


def _yield_the_floor():
    """Release OUR lock — and only ours. Never releases another process's claim.

    THE LOCK WAS NEVER RELEASED (found 2026-08-02, the third stale-lock refusal in one day):
    `_take_the_floor` wrote the file and nothing ever removed it, so every gate — pass or fail —
    orphaned its lock. The design leaned on next-run stale-pid reclaim, but Windows RECYCLES
    pids: a dead gate's number gets claimed by some unrelated live python, `os.kill(pid, 0)`
    reports it alive, and the floor is refused for a process that was never a gate. The tell,
    in hindsight: deploy chains had grown a habitual `rm -f .gate.lock` that nobody questioned —
    a manual ritual compensating for a missing `finally` is a defect wearing a chore's clothes.
    """
    try:
        with open(_LOCK, encoding="utf-8") as fh:
            pid = int((fh.read().split() or ["0"])[0])
        if pid == os.getpid():
            os.remove(_LOCK)
    except (OSError, ValueError):
        pass


def main() -> int:
    if not _take_the_floor():
        return 2
    try:
        return _gated_main()
    finally:
        _yield_the_floor()


def _gated_main() -> int:
    rc = 0
    # 0. The suite must be whole before its result means anything.
    rc |= _suite_is_whole()

    # 1. The moat — the hard gate: 60/60, 0 false-positives (benchmark exits non-zero otherwise).
    rc |= _run([sys.executable, "tools/benchmark.py"])

    # 2. The suite + coverage floor (preferred), else a sovereign fallback.
    #
    # -p vacuity_plugin rides ALONG with the existing run instead of adding a phase. It wraps the
    # corpus doors and fails the session if a test PASSED while asserting against a corpus it
    # never populated — a failure mode pytest cannot see, because the assertion iterates nothing
    # and reports green. That is exactly how the leaked fixture in tests/test_floor.py stayed
    # hidden while the reachability guard reported a number for a card nobody had added to the
    # keeping. One flag, no second suite run. A deliberate empty-corpus test declares itself where
    # it lives:  @pytest.mark.empty_corpus_ok("mints into it")
    ENV["VACUITY_ENFORCE"] = "1"
    ENV["PYTHONPATH"] = os.pathsep.join([os.path.join(ROOT, "src"), os.path.join(ROOT, "tools")])
    _vac = ["-p", "vacuity_plugin"]

    if _has("pytest") and _has("coverage"):
        rc |= _run([sys.executable, "-m", "coverage", "run", "--source=src/concordance",
                    "-m", "pytest", "-q"] + _vac)
        _run([sys.executable, "-m", "coverage", "report"])
        rc |= _run([sys.executable, "-m", "coverage", "report", f"--include={CORE}", f"--fail-under={FLOOR}"])
        # Per-file floor for the two safety-critical stores (the hash-chain + content-addressed
        # store): the aggregate floor can mask a weak individual file, and these two must not slip.
        for _crit in ("*/ledger.py", "*/cas.py"):
            rc |= _run([sys.executable, "-m", "coverage", "report", f"--include={_crit}", f"--fail-under={FLOOR}"])
    elif _has("pytest"):
        print("\n(coverage not installed — running suite without the coverage floor)")
        rc |= _run([sys.executable, "-m", "pytest", "-q"] + _vac)
    else:
        print("\n(pytest not installed — running each test file as a script)")
        for t in sorted(glob.glob(os.path.join(ROOT, "tests", "test_*.py"))):
            rc |= _run([sys.executable, t])

    print("\n=== GATE PASS ===" if rc == 0 else "\n=== GATE FAIL ===", flush=True)
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
