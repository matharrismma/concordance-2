"""THE TICK STICK — infer an open shape from marks you can actually reach (Matt, 2026-10-05).

A joiner fitting a board to a crooked wall does not guess the wall: he lays a stick against it, makes a tick at
every point he can reach, and the shape is inferred from the ticks — exact where there is a tick, honest about
the gaps between. For an OPEN QUESTION (a Millennium problem, or any question the keeping holds open) the stick is
the question, a TICK is a mark the engine can stand behind, and the FIT is what the ticks jointly establish —
stated no further than the marks go. Ticks only accumulate; the fit only tightens; nothing is ever inferred past
the last mark.

Kinds of tick:
    bound        a sealed verification up to a height / size / count ("every zero up to T = 200 is on the line")
                 — carries the ledger seal of the verification that made it; the fit's bound is the greatest
    instance     a sealed verification of one case ("the conjecture holds for this curve")
    witness      a sealed computation that exhibits something (a value, an example)
    equivalence  a CITED theorem: this statement ⇔ that one (a source is required; it is cited, not sealed)
    exclusion    a CITED barrier: proofs of this kind cannot settle the question (a source is required)
    note         a remark by a named author; never counts toward the fit

Sealed kinds (bound, instance, witness) require `seal`: the content hash of a verification in this node's ledger
whose verdict HOLDS — the stick checks it in the keeping before it accepts the tick. Cited kinds require `source`.
Everything is appended to data/sticks.jsonl (data-only; rides with the sync) and folded on read.

Found, never generated: the stick never says "therefore the hypothesis is true". It says: verified to here,
excluded there, open beyond.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

SEALED_KINDS = ("bound", "instance", "witness")
CITED_KINDS = ("equivalence", "exclusion")
KINDS = SEALED_KINDS + CITED_KINDS + ("note",)


def _path(data_dir: Optional[Path] = None) -> Path:
    d = Path(data_dir) if data_dir else Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")
    return d / "sticks.jsonl"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")[:60]


def _append(ev: Dict[str, Any], data_dir: Optional[Path] = None) -> None:
    p = _path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def _events(data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    p = _path(data_dir)
    if not p.exists():
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def fold(data_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    sticks: Dict[str, Dict[str, Any]] = {}
    for ev in _events(data_dir):
        if ev.get("event") == "stick":
            sid = ev["id"]
            sticks[sid] = {"id": sid, "question": ev.get("question"), "statement": ev.get("statement"),
                           "field": ev.get("field"), "references": ev.get("references") or [],
                           "created_at": ev.get("at"), "ticks": []}
        elif ev.get("event") == "tick":
            st = sticks.get(ev.get("stick"))
            if st is not None:
                st["ticks"].append({k: v for k, v in ev.items() if k not in ("event", "stick")})
    return sticks


# ── the fit: what the ticks jointly establish, and no more ──────────────────────────────────────
def fit(stick: Dict[str, Any]) -> Dict[str, Any]:
    ticks = stick.get("ticks") or []
    bounds = [t for t in ticks if t.get("kind") == "bound" and isinstance(t.get("up_to"), (int, float))]
    best = max(bounds, key=lambda t: t["up_to"]) if bounds else None
    instances = [t for t in ticks if t.get("kind") == "instance"]
    witnesses = [t for t in ticks if t.get("kind") == "witness"]
    equivalences = [t for t in ticks if t.get("kind") == "equivalence"]
    exclusions = [t for t in ticks if t.get("kind") == "exclusion"]
    notes = [t for t in ticks if t.get("kind") == "note"]
    out: Dict[str, Any] = {
        "verified_up_to": ({"up_to": best["up_to"], "unit": best.get("unit"), "claim": best.get("claim"), "seal": best.get("seal"),
                            "at": best.get("at")} if best else None),
        "verified_instances": len(instances),
        "witnesses": len(witnesses),
        "equivalent_statements": [t.get("claim") for t in equivalences],
        "excluded_approaches": [t.get("claim") for t in exclusions],
        "record": [{"claim": t.get("claim"), "by": t.get("by"), "at": t.get("at")} for t in notes],
        "sealed_ticks": sum(1 for t in ticks if t.get("kind") in SEALED_KINDS),
        "cited_ticks": sum(1 for t in ticks if t.get("kind") in CITED_KINDS),
        "progression": [{"up_to": t["up_to"], "seal": t.get("seal"), "at": t.get("at")}
                        for t in sorted(bounds, key=lambda t: t["up_to"])],
    }
    if best:
        out["open"] = f"beyond {best.get('unit') or 'the bound'} {best['up_to']:g}: not verified here"
    elif instances or witnesses:
        out["open"] = (f"no sealed bound; {len(instances)} sealed instance(s) and {len(witnesses)} witness(es) — "
                       "the general question stays open")
    else:
        out["open"] = "no sealed bound yet — the stick has only cited marks" if (equivalences or exclusions) else "no marks yet"
    # THE SURVIVING WINDOW (narrow by elimination; Matt, 2026-10-05): every bound, witness and exclusion RULES OUT
    # a region where the question could fail. The window is what those eliminations leave standing — pushed up each
    # rerun. A problem with only cited exclusions (a proof-barrier problem) has no numeric window to shrink, and
    # says so; one with sealed eliminations names the frontier past which it is untested.
    eliminations = []
    if best:
        eliminations.append(f"no failure below {best.get('unit') or 'the bound'} {best['up_to']:g} (direct)")
    for t in instances:                                   # an instance IS an elimination: verified for one case
        eliminations.append("verified for a case: " + (t.get("claim") or "")[:150])
    for t in witnesses:
        eliminations.append((t.get("claim") or "")[:160])
    for t in exclusions:
        eliminations.append("ruled out: " + (t.get("claim") or "")[:150])
    out["window"] = {
        "eliminations": eliminations,
        "surviving": (("a failure, if any, must evade every elimination above at once — the frontier is pushed to "
                       + (f"{best.get('unit') or 'the bound'} {best['up_to']:g}" if best else "the marks listed"))
                      if eliminations else "nothing eliminated yet"),
        "narrows_numerically": bool(best or witnesses),
        "note": ("Narrow by elimination: we chart what the question is NOT, and rerun to push the frontier. Each pass "
                 "that finds no counterexample narrows the surviving window; it is evidence, never a proof. A problem "
                 "whose only marks are cited barriers has no numeric window to shrink — the barriers say which proofs "
                 "cannot settle it, not how far a search has reached."),
    }
    out["note"] = ("The fit is exactly what the ticks establish: a sealed bound, sealed instances, cited equivalences and "
                   "exclusions. It never says the question is settled; it says verified to here, excluded there, open beyond.")
    return out


# ── the doors ───────────────────────────────────────────────────────────────────────────────────
def create(question: str, statement: str = "", field: str = "", references: Optional[List[str]] = None,
           data_dir: Optional[Path] = None) -> Dict[str, Any]:
    q = (question or "").strip()
    if len(q) < 8:
        return {"ok": False, "error": "a stick needs a question (8+ characters)"}
    sid = "stick_" + _slug(q)
    if sid in fold(data_dir):
        return {"ok": True, "id": sid, "existed": True}
    _append({"event": "stick", "id": sid, "question": q[:300], "statement": (statement or "")[:2000],
             "field": (field or "")[:80], "references": [str(r)[:300] for r in (references or [])][:12],
             "at": int(time.time())}, data_dir)
    return {"ok": True, "id": sid, "existed": False}


def _seal_holds(seal: str, data_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """The sealed record for a content hash, if it is in this node's keeping and its verdict HOLDS."""
    from . import cas
    base = (Path(data_dir) / "cas") if data_dir else None
    rec = cas.fetch_anywhere(seal, base_dir=base) if base else cas.fetch_anywhere(seal)
    if not isinstance(rec, dict):
        return None
    verdict = rec.get("verdict") or ((rec.get("gate_results") or [{}])[0].get("details") or {}).get("verdict")
    if verdict != "HOLDS" and rec.get("overall") != "PASS":
        return None
    return rec


def tick(stick_id: str, kind: str, claim: str, *, seal: str = "", source: str = "", up_to: Any = None,
         unit: str = "", by: str = "", data_dir: Optional[Path] = None) -> Dict[str, Any]:
    sticks = fold(data_dir)
    st = sticks.get(stick_id)
    if st is None:
        return {"ok": False, "error": f"no stick {stick_id!r}"}
    kind = (kind or "").strip().lower()
    if kind not in KINDS:
        return {"ok": False, "error": f"kind must be one of {KINDS}"}
    claim = (claim or "").strip()
    if len(claim) < 8:
        return {"ok": False, "error": "a tick needs a claim (8+ characters)"}
    ev: Dict[str, Any] = {"event": "tick", "stick": stick_id, "kind": kind, "claim": claim[:600], "at": int(time.time()),
                          "by": (by or "")[:80]}
    if kind in SEALED_KINDS:
        seal = (seal or "").strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", seal):
            return {"ok": False, "error": "a sealed tick needs `seal`: the 64-hex content hash of a HOLDS verification in this keeping"}
        if _seal_holds(seal, data_dir) is None:
            return {"ok": False, "error": f"seal {seal[:12]}… is not a HOLDS verification in this node's keeping — verify first, then tick"}
        ev["seal"] = seal
        if kind == "bound":
            try:
                ev["up_to"] = float(up_to)
            except (TypeError, ValueError):
                return {"ok": False, "error": "a bound tick needs `up_to` (a number: the height / size / count verified to)"}
            ev["unit"] = (unit or "")[:40]
            prev = [t for t in st["ticks"] if t.get("kind") == "bound" and isinstance(t.get("up_to"), (int, float))]
            if prev and ev["up_to"] <= max(t["up_to"] for t in prev):
                return {"ok": False, "error": f"the stick already has a bound at {max(t['up_to'] for t in prev):g}; a new bound must go further"}
    elif kind in CITED_KINDS:
        source = (source or "").strip()
        if len(source) < 8:
            return {"ok": False, "error": "a cited tick needs `source` (the theorem's paper or book, with year)"}
        ev["source"] = source[:300]
    _append(ev, data_dir)
    st = fold(data_dir)[stick_id]
    return {"ok": True, "stick": stick_id, "tick": ev, "fit": fit(st), "ticks": len(st["ticks"])}


def read(stick_id: str, data_dir: Optional[Path] = None) -> Dict[str, Any]:
    st = fold(data_dir).get(stick_id)
    if st is None:
        return {"ok": False, "error": f"no stick {stick_id!r}", "sticks": sorted(fold(data_dir))}
    return {"ok": True, **st, "fit": fit(st)}


def listing(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    sticks = fold(data_dir)
    rows = []
    for sid, st in sorted(sticks.items()):
        f = fit(st)
        rows.append({"id": sid, "question": st.get("question"), "field": st.get("field"), "ticks": len(st["ticks"]),
                     "verified_up_to": f["verified_up_to"], "excluded": len(f["excluded_approaches"]), "open": f["open"]})
    return {"sticks": rows, "count": len(rows),
            "note": ("A tick stick holds an open question with the marks the engine can stand behind — sealed verifications "
                     "and cited theorems — and the fit they establish, never more. POST /stick to open one; POST /tick to add a mark.")}
