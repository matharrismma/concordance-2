"""Derivation moat — reduce a claim (or a multi-step derivation) to a verdict + trail.

The crown jewel of the engine: it verifies a PROVIDED derivation and hands back
HOLDS / BROKEN / INCOMPLETE. The metric that matters most is the FALSE-POSITIVE rate
— it must never return HOLDS for a falsehood (including removable-singularity traps
like x/x == 1). The engine verifies; it does not generate the answer.

A math step's spec is `{mode, params}`; a non-math step's spec is the domain PACKET
(the artifact keys the domain verifier reads, e.g. {"PHYS_VERIFY": {...}}). Math routes
to the sympy verifiers; every other domain routes to its deterministic fleet verifier via
run_for_domain — on the SECULAR surface only, so the witness verifiers (theology /
scripture / witness — signposts, CONCORDANT-never-HOLDS) can never mint a HOLDS seal here.
Ported from 1.0 api/derivation.py (verify_step/verify_derivation), routed directly to
the 2.0 verifiers (no agent_manifest indirection).
"""
from __future__ import annotations

import concurrent.futures as _futures
import json
import os
import threading as _threading
from typing import Any, Dict, List

from . import verifiers as _verifiers
from .verifiers import mathematics as _math

_TERMINAL_FAIL = ("MISMATCH", "ERROR")

# DoS guards: reject oversized expressions before sympy sees them, and bound compute time
# so a pathological-but-small expression cannot pin a request thread forever.
_MAX_SPEC_CHARS = int(os.environ.get("CONCORDANCE_MAX_EXPR_CHARS", "4000") or 4000)
_VERIFY_TIMEOUT_S = float(os.environ.get("CONCORDANCE_VERIFY_TIMEOUT_S", "8") or 8)


# Bounded, PROCESS-WIDE verify pool: at most _MAX_WORKERS sympy workers run at once. A
# timed-out worker is not killable (sympy is C-bound), so it keeps its slot until it finishes
# — which IS the bound: under a many-IP flood, excess verifications get an immediate "busy"
# ERROR (never HOLDS) instead of piling up unkillable threads that pin every core.
_MAX_WORKERS = max(1, int(os.environ.get("CONCORDANCE_VERIFY_WORKERS", "4") or 4))
_POOL = _futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS, thread_name_prefix="verify")
_SLOTS = _threading.BoundedSemaphore(_MAX_WORKERS)


class _Saturated(Exception):
    """All verify slots are busy — shed load rather than queue unbounded work."""


def _call_with_timeout(fn, arg):
    """Run a verifier with a hard wall-clock bound on a bounded shared pool. result() returns
    control on timeout so the request never hangs; the worker releases its slot when it ends."""
    if not _SLOTS.acquire(blocking=False):
        raise _Saturated()

    def _run():
        try:
            return fn(arg)
        finally:
            _SLOTS.release()

    return _POOL.submit(_run).result(timeout=_VERIFY_TIMEOUT_S)

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
    if len(json.dumps(params, default=str)) > _MAX_SPEC_CHARS:  # DoS guard, before sympy
        return {"status": "ERROR", "detail": f"expression too large (> {_MAX_SPEC_CHARS} chars)"}
    try:
        res = _call_with_timeout(fn, params)  # a VerifierResult, time- and pool-bounded
    except _futures.TimeoutError:
        return {"status": "ERROR", "detail": f"verification timed out (> {_VERIFY_TIMEOUT_S}s)"}
    except _Saturated:
        return {"status": "ERROR", "detail": "verifier busy (too many concurrent verifications) — retry shortly"}
    return {"status": res.status, "detail": (res.detail or "")[:300]}


def _reduce_domain_results(results: List[Any]) -> Dict[str, str]:
    """Reduce a domain's list of VerifierResult to ONE moat status. A contradiction is the
    cardinal signal, so MISMATCH wins over ERROR wins over CONFIRMED; only an all-CONFIRMED
    applicable set is CONFIRMED. No applicable verifier -> NOT_APPLICABLE (an honest gap, an
    INCOMPLETE composite — never a false HOLDS). Mirrors test_fp_gate._status exactly."""
    applicable = [r for r in results if r.applicable]
    if not applicable:
        return {"status": "NOT_APPLICABLE",
                "detail": "no applicable secular verifier for this domain/artifact"}
    mism = [r for r in applicable if r.status == "MISMATCH"]
    if mism:
        return {"status": "MISMATCH", "detail": "; ".join(f"{r.name}: {r.detail}" for r in mism)[:300]}
    errs = [r for r in applicable if r.status == "ERROR"]
    if errs:
        return {"status": "ERROR", "detail": "; ".join(f"{r.name}: {r.detail}" for r in errs)[:300]}
    return {"status": "CONFIRMED",
            "detail": "; ".join(f"{r.name}: {r.detail}" for r in applicable if r.passed)[:300]}


def verify_domain(domain: str, spec: Dict[str, Any]) -> Dict[str, str]:
    """Route a non-math domain claim to its deterministic fleet verifier(s) via
    run_for_domain, on the SECULAR surface only. Same DoS bounds as the math path (size guard
    + shared bounded pool + wall-clock timeout). The FP gate proves 0 false-positives across
    every domain this reaches, so a CONFIRMED here is as trustworthy as a math CONFIRMED."""
    packet = spec or {}
    if len(json.dumps(packet, default=str)) > _MAX_SPEC_CHARS:  # DoS guard, before any verifier
        return {"status": "ERROR", "detail": f"packet too large (> {_MAX_SPEC_CHARS} chars)"}
    try:
        results = _call_with_timeout(
            lambda p: _verifiers.run_for_domain(domain, p, surface="secular"), packet)
    except _futures.TimeoutError:
        return {"status": "ERROR", "detail": f"verification timed out (> {_VERIFY_TIMEOUT_S}s)"}
    except _Saturated:
        return {"status": "ERROR", "detail": "verifier busy (too many concurrent verifications) — retry shortly"}
    return _reduce_domain_results(results)


def verify_step(domain: str, spec: Dict[str, Any]) -> Dict[str, str]:
    """Run one step's verifier and reduce to a single status. Fail closed: a verifier
    that raises becomes ERROR (a failed step), never a crash and never a silent pass.
    Mathematics routes to the sympy moat; every other (secular) domain routes to its
    deterministic fleet verifier."""
    domain = (domain or "").strip().lower()
    if not domain:
        return {"status": "ERROR", "detail": "step missing 'domain'"}
    try:
        if domain in ("mathematics", "math"):
            return verify_math(spec or {})
        return verify_domain(domain, spec or {})
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
