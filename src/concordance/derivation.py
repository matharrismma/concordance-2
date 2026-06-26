"""Derivation moat — reduce a claim (or a multi-step derivation) to a verdict + trail.

The crown jewel of the engine: it verifies a PROVIDED derivation and hands back
HOLDS / BROKEN / INCOMPLETE. The metric that matters most is the FALSE-POSITIVE rate
— it must never return HOLDS for a falsehood (including removable-singularity traps
like x/x == 1). The engine verifies; it does not generate the answer.

A spec is `{mode, params}`; `params` is passed straight to the matching verifier.
Ported from 1.0 api/derivation.py (verify_step/verify_derivation), routed directly to
the 2.0 verifiers (no agent_manifest indirection).
"""
from __future__ import annotations

from typing import Any, Dict, List

from .verifiers import mathematics as _math

_TERMINAL_FAIL = ("MISMATCH", "ERROR")

# math mode -> verifier function. params (the spec body) is passed straight in.
_MATH_MODES = {
    "equality": _math.verify_equality,
    "inequality": _math.verify_inequality,
    "derivative": _math.verify_derivative,
    "integral": _math.verify_integral,
    "limit": _math.verify_limit,
    "solve": _math.verify_solve,
}


def verify_math(spec: Dict[str, Any]) -> Dict[str, str]:
    """Route a `{mode, params}` math spec to its verifier; reduce to a status."""
    mode = (spec.get("mode") or "").strip().lower()
    params = spec.get("params") or {}
    fn = _MATH_MODES.get(mode)
    if fn is None:
        return {"status": "ERROR", "detail": f"unknown math mode {mode!r}"}
    res = fn(params)  # a VerifierResult
    return {"status": res.status, "detail": (res.detail or "")[:300]}


def verify_step(domain: str, spec: Dict[str, Any]) -> Dict[str, str]:
    """Run one step's verifier and reduce to a single status. Fail closed: a verifier
    that raises becomes ERROR (a failed step), never a crash and never a silent pass."""
    domain = (domain or "").strip().lower()
    if not domain:
        return {"status": "ERROR", "detail": "step missing 'domain'"}
    if domain != "mathematics":
        return {"status": "ERROR", "detail": f"unsupported domain {domain!r} (mathematics only, for now)"}
    try:
        return verify_math(spec or {})
    except Exception as exc:  # noqa: BLE001 — fail closed
        return {"status": "ERROR", "detail": f"verifier raised: {type(exc).__name__}: {str(exc)[:200]}"}


def verify_derivation(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify an ordered derivation. The full trail is returned, but the COMPOSITE
    verdict is governed by the FIRST step that breaks — where trust stops."""
    if not isinstance(steps, list) or not steps:
        return {"verdict": "ERROR", "detail": "no steps provided", "trail": []}

    trail: List[Dict[str, Any]] = []
    seen_ids: set = set()
    confirmed_ids: set = set()
    verdict = "HOLDS"
    broken_at = None
    gap_at = None

    for i, step in enumerate(steps):
        sid = str(step.get("id") or f"s{i}")
        domain = str(step.get("domain", ""))
        spec = step.get("spec") or {}
        uses = [str(u) for u in (step.get("uses") or [])]

        missing = [u for u in uses if u not in seen_ids]
        unconfirmed = [u for u in uses if u in seen_ids and u not in confirmed_ids]
        link_ok = not missing and not unconfirmed

        sr = verify_step(domain, spec)
        st = sr["status"]

        entry: Dict[str, Any] = {
            "id": sid, "domain": domain, "claim": str(step.get("claim", "")),
            "uses": uses, "status": st, "detail": sr.get("detail", ""), "link_ok": link_ok,
        }
        if missing:
            entry["missing_refs"] = missing
        if unconfirmed:
            entry["builds_on_unconfirmed"] = unconfirmed
        trail.append(entry)
        seen_ids.add(sid)

        if st == "CONFIRMED" and link_ok:
            confirmed_ids.add(sid)
        elif verdict == "HOLDS":  # first break governs the composite
            if st == "NOT_APPLICABLE":
                verdict, gap_at = "INCOMPLETE", sid
            else:  # MISMATCH / ERROR / broken link
                verdict, broken_at = "BROKEN", sid

    return {
        "verdict": verdict,
        "steps": len(steps),
        "confirmed_steps": len(confirmed_ids),
        "broken_at": broken_at,
        "gap_at": gap_at,
        "trail": trail,
        "note": ("The trail is the trust: each step is machine-verified and may build "
                 "only on confirmed prior steps. The engine verifies a provided "
                 "derivation; it does not generate the answer."),
    }


def verify(spec: Dict[str, Any], domain: str = "mathematics") -> Dict[str, Any]:
    """One-claim convenience: the verdict for a single `{mode, params}` spec."""
    return verify_derivation([{"id": "b", "domain": domain, "spec": spec}])
