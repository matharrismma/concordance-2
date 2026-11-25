"""THE STICK RE-CHECK, the logic (2026-11-25). tools/recheck_sticks.py is its command line; GET /sticks/recheck
serves the same report read-only, so the nightly live assay (nh-assay.timer) and every deploy gate re-read every sealed
mark through one probe. See tools/recheck_sticks.py for what each reading means."""
from __future__ import annotations

import collections
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from . import cas, tickstick as TS

ROOT = Path(__file__).resolve().parent.parent.parent
GOLDEN = ROOT / "tests" / "fixtures" / "tick_golden"
FAILING = ("MISSING", "TAMPERED", "NOT_HOLDS")


def golden_seals(golden_dir: Path = GOLDEN) -> Dict[Tuple[str, str, str], Tuple[str, str]]:
    """{(stick, kind, claim): (seal, entry)} for every sealed mark the current catalog mints."""
    out: Dict[Tuple[str, str, str], Tuple[str, str]] = {}
    for f in sorted(Path(golden_dir).glob("*.json")):
        try:
            g = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for sid, st in (g.get("sticks") or {}).items():
            for t in st.get("ticks") or []:
                if t.get("seal"):
                    out[(sid, str(t.get("kind")), t.get("claim") or "")] = (str(t["seal"]), f.stem)
    return out


def holds(rec: Dict[str, Any]) -> bool:
    if rec.get("overall") == "PASS":
        return True
    gr = rec.get("gate_results") or [{}]
    v = rec.get("verdict") or ((gr[0] if isinstance(gr, list) and gr else {}).get("details") or {}).get("verdict")
    return v == "HOLDS"


def recheck(data_dir: Optional[Path] = None, golden_dir: Path = GOLDEN) -> Dict[str, Any]:
    t0 = time.time()
    sticks = TS.fold(data_dir)
    gold = golden_seals(golden_dir)
    base = (Path(data_dir) / "cas") if data_dir else None
    integrity: collections.Counter = collections.Counter()
    now: collections.Counter = collections.Counter()
    problems = []
    drifted_at = []
    n = 0
    for sid, st in sorted(sticks.items()):
        for t in st.get("ticks") or []:
            if t.get("kind") not in TS.SEALED_KINDS or not t.get("seal"):
                continue
            n += 1
            seal = str(t["seal"])
            try:
                rec = cas.fetch_anywhere(seal, base_dir=base) if base else cas.fetch_anywhere(seal)
            except Exception:  # noqa: BLE001 - an unreadable record is a missing record, reported
                rec = None
            if not isinstance(rec, dict):
                state = "MISSING"
            elif cas.content_hash_of(rec) != seal:
                state = "TAMPERED"
            elif not holds(rec):
                state = "NOT_HOLDS"
            else:
                state = "MATCHES"
            integrity[state] += 1
            g = gold.get((sid, str(t.get("kind")), t.get("claim") or ""))
            if g is None:
                drift = "not_in_catalog"
            elif g[0] == seal:
                drift = "SAME"
            else:
                drift = "DRIFTED"
            now[drift] += 1
            if drift == "DRIFTED" and isinstance(t.get("at"), (int, float)):
                drifted_at.append(int(t["at"]))
            if state in FAILING or drift == "DRIFTED":
                problems.append({"stick": sid, "kind": t.get("kind"), "seal": seal, "integrity": state, "now": drift,
                                 "catalog_entry": g[1] if g else None, "catalog_seal": g[0] if g else None,
                                 "claim": (t.get("claim") or "")[:160], "by": (t.get("by") or "")[:80]})
    failing = [p for p in problems if p["integrity"] in FAILING]
    day = lambda ts: time.strftime("%Y-%m-%d", time.gmtime(ts))  # noqa: E731
    return {
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sticks": len(sticks),
        "sealed_marks": n,
        "integrity": dict(integrity),
        "now": dict(now),
        "ok": not failing,
        "failing": len(failing),
        "drift": {"marks": now.get("DRIFTED", 0),
                  "minted_from": day(min(drifted_at)) if drifted_at else None,
                  "minted_to": day(max(drifted_at)) if drifted_at else None,
                  "means": ("re-minted today, the claim still HOLDS but the record's bytes differ (e.g. a verifier's "
                            "detail wording changed); a re-run of the old entry would add a second mark beside it")},
        "problems": (failing + [p for p in problems if p["integrity"] not in FAILING])[:300],
        "seconds": round(time.time() - t0, 2),
        "note": ("Read-only. integrity: the record is present, hashes to its seal, and HOLDS. now: a mark the current "
                 "catalog mints is SAME as today's seal, or DRIFTED; not_in_catalog is not a failure."),
    }
