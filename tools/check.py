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
FLOOR = "75"


def _run(cmd: list) -> int:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    return subprocess.call(cmd, cwd=ROOT, env=ENV)


def _has(mod: str) -> bool:
    return subprocess.call([sys.executable, "-c", f"import {mod}"], env=ENV,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def main() -> int:
    rc = 0
    # 1. The moat — the hard gate: 58/58, 0 false-positives (benchmark exits non-zero otherwise).
    rc |= _run([sys.executable, "tools/benchmark.py"])

    # 2. The suite + coverage floor (preferred), else a sovereign fallback.
    if _has("pytest") and _has("coverage"):
        rc |= _run([sys.executable, "-m", "coverage", "run", "--source=src/concordance", "-m", "pytest", "-q"])
        _run([sys.executable, "-m", "coverage", "report"])
        rc |= _run([sys.executable, "-m", "coverage", "report", f"--include={CORE}", f"--fail-under={FLOOR}"])
    elif _has("pytest"):
        print("\n(coverage not installed — running suite without the coverage floor)")
        rc |= _run([sys.executable, "-m", "pytest", "-q"])
    else:
        print("\n(pytest not installed — running each test file as a script)")
        for t in sorted(glob.glob(os.path.join(ROOT, "tests", "test_*.py"))):
            rc |= _run([sys.executable, t])

    print("\n=== GATE PASS ===" if rc == 0 else "\n=== GATE FAIL ===", flush=True)
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
