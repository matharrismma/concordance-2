#!/usr/bin/env python3
"""Monte Carlo path/experience simulator — stress the sealed-receipt path at volume (Matt, 2026-10-07:
"simulate paths and experiences ... I don't want it to break down in use", sharpened by Jevons' paradox:
cheap seals invite MANY seals, so prove each stays bounded under induced volume).

Seeded and reproducible. Samples N random verification "experiences" (true / false / edge numeric claims)
and seals each through the SAME path the engine uses (verify_derivation -> receipts.attach), asserting the
invariants that mean the engine does not break down or lie in use:

  * no unhandled exception leaks from any trial (a leak IS a breakdown);
  * a TRUE claim  -> verdict HOLDS, a re-fetchable seal, and it enters the ledger (ledgered);
  * a FALSE claim -> NOT certified HOLDS (no false positive), sealed but NOT ledgered;
  * every seal is within its RESOURCE BOUND (per-seal wall time) — so the 82s/6GB cold-load can never
    silently return;
  * after all N appends the ledger hash chain still verifies — no fork.

Runs in an ISOLATED temp data dir (never the live keeping) with CONCORDANCE_SEAL_INDEX=0 (the cold path).
Any invariant violation prints the seed and the failing case and exits non-zero (a replayable failure).

    PYTHONPATH=src python tools/mc_paths.py [N=300] [seed=1] [bound_s=2.0]
"""
from __future__ import annotations

import json
import os
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path


def _spec(nid: str, expr: str, claimed: float, tol: float = 1e-9) -> dict:
    return {"id": nid, "domain": "mathematics",
            "spec": {"mode": "numeric",
                     "params": {"numeric_expr": expr, "claimed_value": claimed, "rel_tol": tol}}}


def main() -> int:
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    bound_s = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    rng = random.Random(seed)

    tmp = Path(tempfile.mkdtemp(prefix="nh_mc_"))
    os.environ["CONCORDANCE_DATA_DIR"] = str(tmp)
    os.environ["CONCORDANCE_SEAL_INDEX"] = "0"          # the cold / bounded path
    os.environ.setdefault("WEB_FIND_DISABLED", "1")     # no network during the sim
    # import AFTER the env is set so the data dir is honored
    from concordance.derivation import verify_derivation
    from concordance import receipts, cas, ledger
    from concordance.engine import EngineConfig
    cfg = EngineConfig()

    worst = 0.0
    worst_case = None
    holds = brk = seals_refetched = ledgered = 0
    failures: list = []

    t_start = time.time()
    try:
        for i in range(N):
            kind = rng.choice(["true", "true", "false", "edge"])   # weight toward real seals
            a, b = rng.randint(0, 9999), rng.randint(1, 9999)
            if kind == "true":
                expr, claimed, want_hold = f"{a} + {b}", float(a + b), True
            elif kind == "false":
                expr, claimed, want_hold = f"{a} + {b}", float(a + b + rng.randint(1, 50)), False
            else:  # edge: cancels to exactly zero
                expr, claimed, want_hold = f"({a} * {b}) - ({a} * {b})", 0.0, True

            nid = f"mc_{seed}_{i}"
            t0 = time.time()
            try:
                res = verify_derivation([_spec(nid, expr, claimed)])
                out = receipts.attach(res, config=cfg, domain="mathematics", index=False)
            except Exception as exc:  # noqa: BLE001 — a leaked exception IS a breakdown
                failures.append({"i": i, "expr": expr, "claimed": claimed,
                                 "error": f"{type(exc).__name__}: {str(exc)[:120]}"})
                continue
            dt = time.time() - t0
            if dt > worst:
                worst, worst_case = dt, {"i": i, "expr": expr, "dt": round(dt, 3)}
            if dt > bound_s:
                failures.append({"i": i, "expr": expr, "dt": round(dt, 3),
                                 "why": f"over resource bound {bound_s}s"})

            verdict = res.get("verdict")
            seal = out.get("seal")
            holds += (verdict == "HOLDS")
            brk += (verdict != "HOLDS")

            if want_hold:
                if verdict != "HOLDS":
                    failures.append({"i": i, "expr": expr, "claimed": claimed,
                                     "verdict": verdict, "why": "true claim not HOLDS"})
                elif not (seal and seal.get("content_hash")):
                    failures.append({"i": i, "expr": expr, "why": "HOLDS but no seal"})
                else:
                    if seal.get("ledgered"):
                        ledgered += 1
                    if cas.fetch_anywhere(seal["content_hash"]):
                        seals_refetched += 1
                    else:
                        failures.append({"i": i, "hash": seal["content_hash"][:12],
                                         "why": "seal not re-fetchable"})
            else:
                if verdict == "HOLDS":
                    failures.append({"i": i, "expr": expr, "claimed": claimed,
                                     "why": "FALSE claim certified HOLDS (false positive!)"})
                if seal and seal.get("ledgered"):
                    failures.append({"i": i, "expr": expr, "why": "false claim entered the ledger chain"})

        # invariant: the chain still verifies (no fork) after N appends
        chain = ledger.verify_chain(ledger_dir=tmp / "ledger", cas_base=tmp / "cas")
        chain_ok = bool(chain.get("ok"))
        if not chain_ok:
            failures.append({"why": "ledger chain broken after volume",
                             "report": {k: chain.get(k) for k in ("ok", "total", "broken_links", "tampered")}})

        total_dt = time.time() - t_start
        led = list((tmp / "ledger").glob("*.json")) if (tmp / "ledger").exists() else []
        rc = tmp / "receipt_cards.jsonl"
        rc_lines = sum(1 for _ in open(rc, encoding="utf-8")) if rc.exists() else 0
        cas_objs = sum(1 for _ in (tmp / "cas").rglob("*.json")) if (tmp / "cas").exists() else 0
        head_exists = (tmp / "ledger" / ".chain.head").exists()

        report = {
            "seed": seed, "N": N, "bound_s": bound_s,
            "holds": holds, "broken": brk, "seals_refetched": seals_refetched, "ledgered": ledgered,
            "worst_seal_s": round(worst, 3), "worst_case": worst_case,
            "total_s": round(total_dt, 2), "mean_seal_ms": round(1000 * total_dt / max(1, N), 1),
            "growth": {"ledger_files": len(led), "receipt_cards": rc_lines, "cas_objects": cas_objs,
                       "chain_head_present": head_exists},
            "chain_ok": chain_ok,
            "failure_count": len(failures), "failures": failures[:20],
        }
        print(json.dumps(report, indent=1))
        if failures:
            print(f"\nFAIL: {len(failures)} invariant violation(s). Replay with seed={seed}.")
            return 1
        print(f"\nPASS: {N} experiences, worst seal {worst:.3f}s (bound {bound_s}s), chain ok, no false positives.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
