"""THE FOUR GATES — a decision walked RED → FLOOR → BROTHERS → GOD, deterministically (Matt, 2026-10-31: "build
if it adds value", on the March-2026 four-gates-demo whose gates were model prompts returning {pass, reasoning}).

(`gates.py` beside this module is the engine's verdict helpers — ok / quarantine / reject — used by engine.py; this
module is the DECISION protocol over the kernel, the constraints and the village, and takes its own name.)

The FORM is the demo's and the kernel's — sequential, fail-fast, halt at the gate that fails. The MECHANISM is the
engine's, not a model's: nothing here generates a verdict or a reason.
  RED      — the non-negotiables: `constraints.scan` on the action's own words (each hit cited to Scripture); the
             crisis net runs before everything (a cry outranks the protocol, byte-identical, real people first).
  FLOOR    — the protective minimums: the constraint floors (an 'error' halts; a 'warn' rides as a named concern),
             and the FACTS the action rests on — the Conductor convenes the fitting faces (faces.convene) and a
             verified claim that came back BROKEN halts; what the keeping holds is cited as the floor it rests on.
  BROTHERS — real brothers, never a model: an INDEPENDENT witness (witness != author — the kernel's own rule,
             "self-confirmation refused"). Without one the verdict is AWAITING, with the doors where the action can
             meet its witnesses (/mesh/door, /group/contribute). A model cannot stand in for this gate; that is the
             whole reason the gate exists (Deuteronomy 19:15; Proverbs 11:14).
  GOD      — never a PASS or HALT from the machine: the Shepherd offers Scripture on authority, timing and calling,
             cited, and the ones who walked it; the question is RETURNED to the person (Proverbs 9:10). The deciding
             stays theirs.
Output is a trail the Console renders in one frame, and a record shaped for the receipt path (never sealed here).
Dependencies are injectable for tests; they default to the live specialists.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

GATES = ("RED", "FLOOR", "BROTHERS", "GOD")
MESH_DOOR = "/mesh/door"              # leave the action on your door for the fellowship to witness
GROUP_DOOR = "/group/contribute"      # or bring it to your study group
_BROKEN = {"BROKEN", "MISMATCH", "FAIL", "FAILED", "FALSE", "REFUTED", "REJECT"}
_HOLDS = {"HOLDS", "PASS", "CONFIRMED", "VERIFIED", "TRUE"}


def _ident(x: Any) -> str:
    """The identity a witness or author is compared by: an id, a name, a public key — lower-cased, or ''."""
    if isinstance(x, dict):
        for k in ("id", "public_key", "key", "name", "node"):
            if x.get(k):
                return str(x[k]).strip().lower()
        return ""
    return str(x or "").strip().lower()


def _skip(rest: List[str], why: str) -> List[Dict[str, Any]]:
    return [{"gate": g, "status": "SKIPPED", "reasons": [why]} for g in rest]


def run(action: str, *, config: Any = None, witness: Any = None, author: Any = None,
        crisis_fn: Optional[Callable[[str], bool]] = None,
        scan_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
        convene_fn: Optional[Callable[..., Dict[str, Any]]] = None,
        shepherd_fn: Optional[Callable[..., Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Walk one proposed action through the four gates. Returns {"kind", "action", "gates": [...], "verdict",
    "halted_at", "record", "means"}; every reason is the constraint's, the kernel's, or a face's — none is authored."""
    action = " ".join((action or "").split())
    if not action:
        return {"error": "action required"}
    at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    digest = hashlib.sha256(action.encode("utf-8")).hexdigest()
    base = {"kind": "gates", "action": action, "action_sha256": digest, "at": at}

    # 0. CRISIS FIRST — a cry outranks the protocol (help-first, never overridden, byte-identical response).
    _is_crisis = crisis_fn or (lambda t: __import__("concordance.ask", fromlist=["is_crisis"]).is_crisis(t))
    if _is_crisis(action):
        return {**base, "kind": "crisis", "handoff": "crisis", "gates": [], "verdict": "CRISIS",
                "means": "a cry outranks the gates — this is handed to the crisis response, real people first"}

    trail: List[Dict[str, Any]] = []

    # 1. RED — the non-negotiables, scanned on the action's own words, each cited.
    scan = (scan_fn or _default_scan)(action)
    if scan.get("red"):
        hits = scan["red"]
        trail.append({"gate": "RED", "status": "HALT",
                      "reasons": [f"{h.get('id')} {h.get('name')} — matched {h.get('matched')!r}" for h in hits],
                      "cites": [h.get("cite") for h in hits if h.get("cite")]})
        trail += _skip(list(GATES[1:]), "halted at RED")
        return _finish(base, trail, "HALTED", "RED")
    trail.append({"gate": "RED", "status": "PASS", "reasons": ["no absolute prohibition named in the action"],
                  "cites": []})

    # 2. FLOOR — the protective minimums: constraint floors, then the facts the action rests on.
    if scan.get("floor_error"):
        hits = scan["floor_error"]
        trail.append({"gate": "FLOOR", "status": "HALT",
                      "reasons": [f"{h.get('id')} {h.get('name')} — matched {h.get('matched')!r}" for h in hits],
                      "cites": [h.get("cite") for h in hits if h.get("cite")]})
        trail += _skip(list(GATES[2:]), "halted at FLOOR")
        return _finish(base, trail, "HALTED", "FLOOR")
    concerns = [f"{h.get('id')} {h.get('name')}: {h.get('cite')}" for h in (scan.get("floor_warn") or scan.get("warnings") or [])]
    floor: Dict[str, Any] = {"gate": "FLOOR", "status": "PASS", "reasons": [], "cites": [], "concerns": concerns,
                             "rests_on": [], "faces": []}
    try:
        panel = (convene_fn or _default_convene)(action, k=2, config=config)
    except Exception as e:  # noqa: BLE001 — the keeping unreachable is a GAP, not a verdict
        panel = {"error": str(e)[:120]}
    seats = (panel or {}).get("panel") or []
    for seat in seats:
        served = (seat or {}).get("served") or {}
        verify = served.get("verify") or {}
        verdict = str(verify.get("verdict") or "").upper()
        name = seat.get("expert") or served.get("name") or seat.get("id")
        if verdict in _BROKEN:
            trail.append({"gate": "FLOOR", "status": "HALT",
                          "reasons": [f"a fact the action rests on does not hold — {name}: {verify.get('detail') or verdict}"],
                          "cites": [c.get("id") for c in served.get("gathered") or [] if isinstance(c, dict) and c.get("id")][:3],
                          "concerns": concerns})
            trail += _skip(list(GATES[2:]), "halted at FLOOR")
            return _finish(base, trail, "HALTED", "FLOOR")
        for c in (served.get("gathered") or [])[:2]:
            if isinstance(c, dict) and c.get("id"):
                floor["rests_on"].append({"id": c.get("id"), "title": c.get("title"), "face": name})
                floor["cites"].append(c.get("id"))
        voice = served.get("voice") or {}
        floor["faces"].append({"id": seat.get("id"), "expert": name,
                               "verdict": verdict or None,
                               "boundary": voice.get("boundary"), "refer": voice.get("refer")})
    if not seats:
        floor["reasons"].append("the keeping could not be consulted — the facts it rests on are unverified (an honest gap, not a floor)")
    elif floor["rests_on"]:
        floor["reasons"].append("no fact the action rests on came back broken; what the keeping holds is cited")
    else:
        floor["reasons"].append("the fitting faces found nothing checkable — the floor is the constraints alone")
    if concerns:
        floor["reasons"].append("named concerns ride along, not vetoes")
    trail.append(floor)

    # 3. BROTHERS — an independent witness, or AWAITING. Never a model.
    w, a = _ident(witness), _ident(author)
    if not w:
        trail.append({"gate": "BROTHERS", "status": "AWAITING",
                      "reasons": ["no independent witness yet — the brothers are real people, not a model"],
                      "cites": ["Deuteronomy 19:15; Proverbs 11:14"], "doors": [MESH_DOOR, GROUP_DOOR]})
        trail += _skip(["GOD"], "reached only with a witness")
        return _finish(base, trail, "AWAITING WITNESS", "BROTHERS")
    if a and w == a:
        trail.append({"gate": "BROTHERS", "status": "AWAITING",
                      "reasons": ["witness == author — self-confirmation refused (the kernel's rule)"],
                      "cites": ["Deuteronomy 19:15; John 7:51"], "doors": [MESH_DOOR, GROUP_DOOR]})
        trail += _skip(["GOD"], "reached only with an independent witness")
        return _finish(base, trail, "AWAITING WITNESS", "BROTHERS")
    trail.append({"gate": "BROTHERS", "status": "PASS",
                  "reasons": [f"witnessed by {w} — independent of the author"],
                  "cites": ["Deuteronomy 19:15"], "witness": witness if isinstance(witness, dict) else {"id": w}})

    # 4. GOD — returned to the person with Scripture offered, never pronounced.
    try:
        served = (shepherd_fn or _default_shepherd)(action, config=config)
    except Exception as e:  # noqa: BLE001
        served = {"error": str(e)[:120]}
    served = served or {}
    passages = [{"id": c.get("id"), "title": c.get("title"), "source": c.get("source") or c.get("shelf")}
                for c in (served.get("gathered") or [])[:3] if isinstance(c, dict)]
    voice = served.get("voice") or {}
    trail.append({"gate": "GOD", "status": "RETURNED",
                  "reasons": ["the deciding is yours — Scripture offered on authority, timing and calling; no verdict from the machine"],
                  "cites": ["Proverbs 9:10"] + [p["id"] for p in passages if p.get("id")],
                  "passages": passages, "offering": served.get("offering"),
                  "voice": {k: voice.get(k) for k in ("found", "offering", "beyond", "close") if voice.get(k)}})
    return _finish(base, trail, "RETURNED", None)


def _finish(base: Dict[str, Any], trail: List[Dict[str, Any]], verdict: str, halted_at: Optional[str]) -> Dict[str, Any]:
    means = {
        "HALTED": f"halted at {halted_at} — the action does not proceed; a corrected version may re-enter and be re-gated",
        "AWAITING WITNESS": "the hard floors held; the action now goes to real brothers for witness — the engine does not stand in for them",
        "RETURNED": "the hard floors held and the action was witnessed; the final gate is yours, with the Word opened to it",
    }[verdict]
    return {**base, "gates": trail, "verdict": verdict, "halted_at": halted_at,
            "record": {"kind": "decision", "action_sha256": base["action_sha256"], "at": base["at"],
                       "gates": [{"gate": g["gate"], "status": g["status"]} for g in trail], "verdict": verdict},
            "means": means + " — found and cited, never generated"}


# ── the live specialists (defaults) ────────────────────────────────────────────────────────────────

def _default_scan(text: str) -> Dict[str, Any]:
    from . import constraints
    return constraints.scan(text)


def _default_convene(text: str, k: int = 2, config: Any = None) -> Dict[str, Any]:
    from . import faces
    return faces.convene(text, k=k, config=config)


def _default_shepherd(text: str, config: Any = None) -> Dict[str, Any]:
    from . import faces
    return faces.compose("face_shepherd", text, config)
