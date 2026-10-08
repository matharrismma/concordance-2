#!/usr/bin/env python3
"""THE FRONT-DOOR BENCHMARK — does a sentence reach the engine? (2026-10-07)

The standing benchmarks (tools/benchmarks.py) hand every verifier a structured PACKET and prove 80/80
domains seal their truth and refuse their falsehood. The front door hands the engine a SENTENCE. Between
the two sits one layer — audit.extract(), the text->packet funnel — and until today nothing measured it.
Measured live on 2026-10-07: 3 of 10 reasonable claims reached a verifier, and one of those was a false
MISMATCH. The gate was green because it was not pointing at the piece that was missing.

This runs every claim in data/frontdoor_claims.json (natural phrasing, each true claim with a false twin)
through the real funnel — audit.audit(text, seal=False): extract -> verify_derivation — and measures:

  reached          an extractor handed the claim to a verifier (claims_found > 0)
  correct          reached AND (a true claim CONFIRMED with no MISMATCH | a false claim MISMATCHED/ERRORed)
  false_positive   a FALSE claim CONFIRMED and never MISMATCHED  — the cardinal failure; must be 0
  false_negative   a TRUE claim reached but MISMATCHED           — the engine calling truth false (9.81)
  found            NOT reached, but the keeping's own sourced table holds the lookup fact the words name
                   (factfind.find_fact: a half-life, a boiling point, an atomic weight) — cited, no receipt.
                   ITS OWN COLUMN (2026-10-07): a found fact never counts as reached, correct, or the floor —
                   widening the reach metric to include lookups is a decision, not a side effect. Reported:
                   found_correct (agrees == truth), found_false_positive (a false claim agreed with — reported,
                   not yet gated), found_wrong (a true claim disagreed with).
  missed           neither reached nor found — an honest miss, named, never a verdict

THE RATCHET (as benchmarks.py's): the floor is every claim that has EVER been reached-and-correct. A
regression is a floor claim that is not correct tonight, or any false positive. `--gate` exits 1 on
regression so the deploy refuses itself. No corpus, no seal, no network: extract + fleet + moat only, so
it runs cold on the memory-bound box in seconds.

    PYTHONPATH=src python tools/frontdoor.py            # run, write data/frontdoor.json, print the summary
    PYTHONPATH=src python tools/frontdoor.py --gate     # same; exit 1 on regression
    PYTHONPATH=src python tools/frontdoor.py --dry-run  # run, print, write nothing
    PYTHONPATH=src python tools/frontdoor.py --verbose  # one line per claim
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", str(ROOT / "data"))


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))


def judge(claim: Dict[str, Any], report: Dict[str, Any], fact: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """One claim's outcome from one audit report, plus (for an unreached claim) the found fact, if any. Pure."""
    truth = bool(claim.get("truth"))
    results = report.get("results") or []
    statuses = [str(r.get("status") or "") for r in results]
    reached = int(report.get("claims_found") or 0) > 0
    confirmed = any("CONFIRM" in s for s in statuses) and not any("MISMATCH" in s for s in statuses)
    refused = any(("MISMATCH" in s or "ERROR" in s) for s in statuses)
    false_pos = reached and (not truth) and confirmed
    false_neg = reached and truth and any("MISMATCH" in s for s in statuses)
    correct = reached and ((truth and confirmed) or ((not truth) and refused))
    # the found-fact column: only for a claim no verifier reached; `agrees` None (nothing claimed) judges nothing
    fact = fact if (isinstance(fact, dict) and fact.get("field")) else None
    found = (not reached) and fact is not None
    agrees = fact.get("agrees") if found else None
    row = {"id": claim["id"], "truth": truth, "reached": reached, "correct": bool(correct),
           "false_positive": bool(false_pos), "false_negative": bool(false_neg),
           "found": bool(found),
           "found_correct": bool(found and agrees is not None and bool(agrees) == truth),
           "found_false_positive": bool(found and (not truth) and agrees is True),
           "found_wrong": bool(found and truth and agrees is False),
           "extractors": [r.get("extractor") for r in results], "domains": [r.get("domain") for r in results],
           "statuses": statuses, "detail": (results[0].get("detail") if results else "")[:200]}
    if found:
        row["fact"] = {k: fact.get(k) for k in ("subject", "property", "value", "unit", "uncertainty", "claimed",
                                                 "claimed_unit", "stated_sigfigs", "agrees", "source")}
    return row


def bench(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from concordance import audit as _audit
    from concordance import factfind as _ff
    out = []
    for c in claims:
        text = str(c["text"])
        try:
            rep = _audit.audit(text, None, seal=False)
        except Exception as e:  # noqa: BLE001 — a crash is a finding, never a silent pass
            rep = {"claims_found": 1, "results": [{"status": f"CRASH:{type(e).__name__}", "detail": str(e)[:200]}]}
        fact = None
        if not int(rep.get("claims_found") or 0):
            try:
                fact = _ff.find_fact(text)                 # pure: the sourced tables only, no corpus
            except Exception as e:  # noqa: BLE001 — a crash in the find is a finding too
                fact = {"field": "crash", "agrees": None, "subject": f"CRASH:{type(e).__name__}", "property": str(e)[:120]}
        out.append(judge(c, rep, fact))
    return out


def run(dry_run: bool = False, data_dir: Optional[Path] = None, claims_path: Optional[Path] = None,
        verbose: bool = False) -> Dict[str, Any]:
    t0 = time.time()
    data = Path(data_dir) if data_dir else _data_dir()
    cpath = Path(claims_path) if claims_path else data / "frontdoor_claims.json"
    out_path = data / "frontdoor.json"
    floor_path = data / "frontdoor.floor.json"
    claims = (json.loads(cpath.read_text(encoding="utf-8")).get("claims") or []) if cpath.exists() else []
    rows = bench(claims)
    prev: Dict[str, Any] = {}
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            prev = {}
    floor: List[str] = []
    if floor_path.exists():
        try:
            floor = list(json.loads(floor_path.read_text(encoding="utf-8")).get("claims") or [])
        except (OSError, ValueError):
            floor = []
    correct_now = {r["id"] for r in rows if r["correct"]}
    floor_set = set(floor) | correct_now
    by_id = {r["id"]: r for r in rows}
    regressions = sorted(i for i in floor_set if i in by_id and not by_id[i]["correct"])
    regressions += [f"false positive: {r['id']}" for r in rows if r["false_positive"]]
    n = len(rows)
    reached = sum(1 for r in rows if r["reached"])
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host": socket.gethostname(), "seconds": round(time.time() - t0, 1),
        "claims": n, "reached": reached, "correct": len(correct_now),
        "false_positives": sum(1 for r in rows if r["false_positive"]),
        "false_negatives": sorted(r["id"] for r in rows if r["false_negative"]),
        # the found-fact column (2026-10-07): beside reach, never inside it — see the module docstring
        "found": sum(1 for r in rows if r["found"]),
        "found_correct": sum(1 for r in rows if r["found_correct"]),
        "found_false_positives": sum(1 for r in rows if r["found_false_positive"]),
        "found_wrong": sorted(r["id"] for r in rows if r["found_wrong"]),
        "missed": sorted(r["id"] for r in rows if not r["reached"] and not r["found"]),
        "newly_correct": sorted(correct_now - set(floor)),
        "regressions": regressions, "regressed": bool(regressions),
        "floor": len(floor_set),
        "previous": {"generated_at": prev.get("generated_at"), "reached": prev.get("reached"),
                     "correct": prev.get("correct")},
        "rows": rows,
        "about": ("Natural-language claims through the real front-door funnel (audit.extract -> verifiers), "
                  "each true claim with a false twin; reach, correctness, false positives (must be 0) and "
                  "false negatives, ratcheted against every claim ever reached-and-correct. A claim no verifier "
                  "reached but the keeping's sourced tables hold (factfind) is counted in its own `found` column, "
                  "never in reach, correct or the floor. Never typed in."),
    }
    if verbose:
        for r in rows:
            if r["correct"]:
                mark = "OK "
            elif r["false_positive"]:
                mark = "FP!"
            elif r["false_negative"]:
                mark = "FN "
            elif r["found_correct"]:
                mark = "FF "
            elif r["found_false_positive"] or r["found_wrong"]:
                mark = "FX!"
            elif r["found"]:
                mark = "F? "
            elif not r["reached"]:
                mark = "-- "
            else:
                mark = "?? "
            if r["found"]:
                f = r["fact"]
                what = f"found: {f.get('subject')} {f.get('property')} = {f.get('value')} {f.get('unit') or ''} agrees={f.get('agrees')}"
            else:
                what = f"{','.join(r['statuses']) or 'missed':<22} {','.join(x or '' for x in r['extractors'])}"
            print(f"  {mark} {r['id']:<14} reached={str(r['reached']):<5} {what}")
    if not dry_run:
        data.mkdir(parents=True, exist_ok=True)
        tmp = out_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, out_path)
        floor_path.write_text(json.dumps({"claims": sorted(floor_set),
                                          "updated_at": summary["generated_at"]}, indent=1), encoding="utf-8")
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    s = run(dry_run="--dry-run" in a, verbose="--verbose" in a)
    print(f"{s['generated_at']} FRONTDOOR {'REGRESSED' if s['regressed'] else 'OK'}: reached {s['reached']}/{s['claims']}, "
          f"correct {s['correct']}/{s['claims']}, false positives {s['false_positives']}, "
          f"false negatives {s['false_negatives']}, found {s['found']} (correct {s['found_correct']}, "
          f"false positives {s['found_false_positives']}, wrong {s['found_wrong']}), missed {len(s['missed'])}, "
          f"newly correct {s['newly_correct']}, regressions {s['regressions']}; {s['seconds']}s")
    if "--gate" in a and s["regressed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
