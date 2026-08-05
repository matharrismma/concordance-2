# The Benchmark, Published — the bound behind "0 false positives" (v1.0.0)

Task #126 (assessment F-11): a universal zero-false-positive claim is stronger than a finite
benchmark can establish. So the claim is BOUNDED, and the bound is this package.

**The claim, correctly worded:** 0 false positives on the published 60-case derivation-moat
benchmark, v1.0.0, re-run on every gate.

**Reproduce it:**
```
PYTHONPATH=src python tools/benchmark.py --json
```
Machine-readable output: every case with its mode, ground-truth label, verdict, and correctness;
false positives and false negatives reported SEPARATELY (a missed truth is never hidden inside
an accuracy figure); totals; the benchmark version.

**What it measures:** 60 ground-truth-labelled claims (30 true, 30 deliberately false) across
equality, inequality, and derivative modes — ported verbatim from 1.0's public benchmark. The
metric that matters is the false-positive count: did the engine ever seal a falsehood. The gate
(`tools/check.py`) runs this before the suite and fails the build on any FP.

**What it does NOT establish:** anything beyond these 60 cases and these three modes. The other
~70 verifier domains are covered by the test suite (170 files, per-domain), not by this
benchmark. Growing the benchmark bumps its version; claims cite the version they were measured
against.

**Mutation evidence:** the gate fails when a verifier breaks (the benchmark exits non-zero on
any FP and the suite's per-domain tests catch behavioral drift) — a green run is load-bearing,
not decorative.
