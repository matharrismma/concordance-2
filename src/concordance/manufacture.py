"""The Conductor's shop-domain CALC door (M2).

Turn one engineering claim + its numbers into a sealed, re-checkable record with a disposition, by
routing through organs this engine already owns — never rebuilding them:

    verify  -> derivation.verify_derivation   (routes a {domain:"manufacturing"} step to
                verifiers/manufacturing.py: sigma level, SPC limits, Cp/Cpk, RSS tolerance stack)
    seal    -> receipts.attach                 (content-addressed seal + hash-chained ledger entry,
                PASS-only — reuses cas + ledger untouched)

This is the sibling of the work-ORDER gate in conductor/engine_bridge.py (RED spindle limits, FLOOR
margins): the order is gated there, the numbers are sealed here. Together they are the Conductor —
the thin manufacturing face CONNECTING to the engine, which is why this lives engine-side and depends
only on engine organs (the conductor package depends on the engine, never the reverse).

The disposition grammar is the one the engineer already uses on an EWP/work package — CALCULATED /
CONTROLLED / PROVISIONAL / OPEN. The engine VERIFIES the calc behind a claim; it never INVENTS or
upgrades the engineer's label (a generator picking its own path is a destructive act). It reports what
the arithmetic EARNED and leaves the decision with the person.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

# The engineer's disposition grammar (from the TBR/EWP work packages).
DISPOSITIONS = ("CALCULATED", "CONTROLLED", "PROVISIONAL", "OPEN")

# What the engine's verdict EARNS for the calc — never an upgrade of the engineer's own label.
# SYSTEM_ERROR is OUR failure, not the claim's, so it stays OPEN and is never REFUSED.
_VERDICT_TO_EARNED = {
    "HOLDS": "CALCULATED",       # the arithmetic is sealed; the engineer may advance it to CONTROLLED
    "BROKEN": "REFUSED",         # the numbers disagree — a miss stays a miss
    "INCOMPLETE": "OPEN",        # not enough present to check
    "SYSTEM_ERROR": "OPEN",      # the engine could not check — says nothing about the claim
}

# Which MFG_VERIFY check a calc selects, by the keys it carries (mirrors manufacturing.py _RULES).
_CALC_SHAPES = (
    (("tolerances", "claimed_rss"), "tolerance_stack_rss"),
    (("dpmo", "claimed_sigma"), "sigma_level"),
    (("mean", "sigma", "claimed_ucl", "claimed_lcl"), "spc_control_limits"),
    (("usl", "lsl", "process_mean", "process_sigma", "claimed_cp_capable"), "process_capability"),
)


def _calc_kind(calc: Dict[str, Any]) -> str:
    for keys, name in _CALC_SHAPES:
        if all(k in calc for k in keys):
            return name
    return "unknown"


def _disposition_line(claimed: Optional[str], verdict: str) -> str:
    if verdict == "HOLDS":
        tail = (" (the engineer claimed %s)" % claimed) if claimed else ""
        return "the calc is CALCULATED and sealed; the engineer may advance it to CONTROLLED" + tail
    if verdict == "BROKEN":
        return "the numbers do not agree — REFUSED; a miss stays a miss, fix the calc before any disposition"
    return "the engine could not check this calc — it stays OPEN (nothing is implied about the claim)"


def manufacture(claim: str, calc: Dict[str, Any], *, disposition: Optional[str] = None,
                config=None) -> Dict[str, Any]:
    """Route a manufacturing claim + its MFG_VERIFY numbers through verify -> seal -> ledger.

    claim        one sentence naming the engineering disposition, e.g. "the magnetic-gap RSS
                 tolerance closure is 0.094 mm".
    calc         an MFG_VERIFY spec dict: {"tolerances":[...], "claimed_rss":...} |
                 {"dpmo":..., "claimed_sigma":...} | {"mean","sigma","claimed_ucl","claimed_lcl"} |
                 {"usl","lsl","process_mean","process_sigma","claimed_cp_capable"}.
    disposition  the engineer's claimed label (optional), one of DISPOSITIONS — carried for the
                 record, never trusted and never upgraded by the engine.
    """
    from . import ask as _ask, receipts
    from .config import EngineConfig
    from .derivation import verify_derivation

    claim = (claim or "").strip()
    if not claim:
        return {"ok": False, "error": "a manufacturing claim (one sentence) is required"}
    if not isinstance(calc, dict) or not calc:
        return {"ok": False, "error": "calc must be a non-empty MFG_VERIFY spec dict"}

    # CRISIS first, always — the engine's order. A shop calc is never a person in danger, but we ask.
    if _ask.is_crisis(claim):
        return {"ok": True, "kind": "crisis", "verdict": "HALT",
                "note": "this reads as a person in danger, not a shop calc — stop and get real help first",
                "resources": list(getattr(_ask, "_CRISIS_RESOURCES", ()))}

    claimed = (disposition or "").strip().upper() or None
    if claimed and claimed not in DISPOSITIONS:
        return {"ok": False, "error": "disposition must be one of %s" % (DISPOSITIONS,)}

    res = verify_derivation([{"id": "mfg", "domain": "manufacturing",
                              "spec": {"MFG_VERIFY": calc}, "claim": claim}])
    verdict = res.get("verdict", "SYSTEM_ERROR")
    trail = res.get("trail") or []
    detail = (trail[0].get("detail", "") if trail else res.get("detail", ""))

    out: Dict[str, Any] = {
        "ok": True,
        "claim": claim,
        "calc_kind": _calc_kind(calc),
        "verdict": verdict,
        "disposition_claimed": claimed,
        "disposition_earned": _VERDICT_TO_EARNED.get(verdict, "OPEN"),
        "disposition": _disposition_line(claimed, verdict),
        "detail": detail,
        "seal": None,
        "cite_url": None,
        "ledgered": False,
    }
    # Seal + ledger ONLY on HOLDS — receipts.attach stores the CAS seal and (PASS-only) the
    # hash-chained ledger entry; a BROKEN or INCOMPLETE calc earns no seal.
    if verdict == "HOLDS":
        sealed = receipts.attach(res, config=config or EngineConfig(), domain="manufacturing")
        seal = sealed.get("seal") or {}
        out["seal"] = seal.get("content_hash")
        out["cite_url"] = seal.get("cite_url")
        out["ledgered"] = bool(seal.get("ledgered"))
        if sealed.get("seal_error"):
            out["seal_error"] = sealed.get("seal_error")
    return out
