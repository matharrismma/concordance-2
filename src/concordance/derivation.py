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
import copy
import json
import logging
import os
import threading as _threading
from typing import Any, Dict, List, Tuple

from . import cells as _cells
from . import verifiers as _verifiers
from .validate import canonical_json_bytes, sha256_bytes
from .verifiers import bridges as _bridges
from .verifiers import mathematics as _math
from .verifiers.base import NeedsTheKeeping, PowerFloorRefused

_log = logging.getLogger("concordance")
_TERMINAL_FAIL = ("MISMATCH", "ERROR")


def _spec_hash(spec: Any) -> str:
    """Canonical SHA-256 of the exact artifact a step verified — the binding that ties a seal
    to WHAT was checked, not merely to a human-supplied label. Two steps that verify different
    specs can never share a spec_hash, so a HOLDS seal cannot be transplanted onto a different
    claim; a re-fetcher can rehash the spec they hold and confirm it is the one that was checked.
    Best-effort: an unserializable spec hashes its repr rather than raising."""
    try:
        return sha256_bytes(canonical_json_bytes(spec if isinstance(spec, dict) else {"_": spec}))
    except Exception:  # noqa: BLE001 — a fingerprint must never break a verdict
        return sha256_bytes(repr(spec).encode("utf-8"))


def _set_spec_path(spec: Dict[str, Any], path: str, value: Any) -> None:
    """Set spec[...path...] = value for value-binding (3b). `path` is a dotted key into the spec —
    "field", "WRAPPER.field", or "params.field" (depth-bounded). Intermediate non-dicts are replaced
    with dicts. Mutates `spec` (always a caller-owned deep copy)."""
    parts = [p for p in str(path).split(".") if p]
    if not parts:
        return
    d = spec
    for p in parts[:-1]:
        nxt = d.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            d[p] = nxt
        d = nxt
    d[parts[-1]] = value

# DoS guards: reject oversized expressions before sympy sees them, and bound compute time
# so a pathological-but-small expression cannot pin a request thread forever.
_MAX_SPEC_CHARS = int(os.environ.get("CONCORDANCE_MAX_EXPR_CHARS", "4000") or 4000)
_VERIFY_TIMEOUT_S = float(os.environ.get("CONCORDANCE_VERIFY_TIMEOUT_S", "8") or 8)


# Bounded, PROCESS-WIDE verify pool: at most _MAX_WORKERS reads run at once, and excess verifications
# get an immediate "busy" ERROR (never HOLDS) instead of piling up. With cells on (serve) a read runs in
# a process that is killed at the window, so no slot outlives its cell (cells.py). Library use stays on
# threads: a thread cannot be killed, so one that timed out keeps its slot until it finishes, and a read
# that holds Python's global lock stops every thread in the process until it ends, the window with them.
_MAX_WORKERS = max(1, int(os.environ.get("CONCORDANCE_VERIFY_WORKERS", "4") or 4))
_POOL = _futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS, thread_name_prefix="verify")
_SLOTS = _threading.BoundedSemaphore(_MAX_WORKERS)
_Saturated = _cells.Saturated


class _NotCheckable(Exception):
    """The power floor refused this claim's check. It was not checked, so it reads as a gap."""


def _call_with_timeout(fn, *args):
    """Run a verifier with a hard wall-clock bound on a bounded shared pool: in a cell when cells are
    on, else on a thread, where result() returns control on timeout and the worker releases its slot
    when it ends. A power the floor refused ends here: the claim reads as not checkable. A read that
    needs the keeping comes back from its cell and runs on the thread path, under its window and slots."""
    cells = _cells.active()
    if cells is not None:
        try:
            return cells.call(fn, args, _VERIFY_TIMEOUT_S)
        except PowerFloorRefused as refused:
            raise _NotCheckable(str(refused)) from None
        except NeedsTheKeeping:
            pass
    if not _SLOTS.acquire(blocking=False):
        raise _Saturated()

    def _run():
        try:
            return fn(*args)
        except PowerFloorRefused as refused:
            raise _NotCheckable(str(refused)) from None
        finally:
            _SLOTS.release()

    return _POOL.submit(_run).result(timeout=_VERIFY_TIMEOUT_S)


# The heavy scientific C-extensions the fleet lazy-imports on first use. If the FIRST heavy
# verification in a fresh worker pays that import INSIDE the wall-clock bound, it can — under
# load — exceed it and turn a TRUE claim into a transient ERROR (errs SAFE, never a false HOLDS,
# but a false negative all the same). warm() pre-pays it at BOOT, outside the timed path.
_HEAVY_LIBS = ("sympy", "sympy.physics.units", "numpy", "scipy.stats", "scipy.optimize", "scipy.linalg", "scipy.special")
# What a read imports on first use and no domain names, so a cell holds it before its first read too.
_CELL_MODULES = ("verifiers.riemann_accel", "verifiers.scripture", "verifiers.spec", "strongs", "pronounce", "thesaurus",
                 "corpus")


def warm() -> None:
    """Pre-import the heavy verify deps at boot so no request pays a cold C-extension import
    inside the per-verification timeout. Best-effort: a minimal sovereign install without these
    still boots (the affected domains simply return NOT_APPLICABLE, never a false result). With cells
    on the reads are not here, so nothing is: a cell has its own preload, and the front stays light."""
    if _cells.active() is not None:
        _log.info("verify deps stay out of the front: reads run in cells")
        return
    import importlib
    warmed = []
    try:
        _math._ensure_sympy()       # the one way sympy loads, so its first load carries the power floor
    except Exception:  # noqa: BLE001 — warming is optional
        pass
    for lib in _HEAVY_LIBS:
        try:
            importlib.import_module(lib)
            warmed.append(lib)
        except Exception:  # noqa: BLE001 — warming is optional
            pass
    _log.info("verify deps warmed: %s", ", ".join(warmed) or "(none available)")


def cell_preload() -> Tuple[str, ...]:
    """What a cell has loaded before its first read, so no read pays for an import inside its window."""
    verifiers = sorted({path for path in _verifiers.VERIFIERS.values() if path.startswith(__package__ + ".")})
    return (*_HEAVY_LIBS, __name__, *verifiers, *(f"{__package__}.{name}" for name in _CELL_MODULES))


def use_cells() -> None:
    """Send every read from here on to a cell (cells.py). serve() and serve_many() call this before the warm;
    importing never does, so a script that imports the engine starts no process. One cell starts now, off any
    request."""
    _cells.enable(_MAX_WORKERS, warm=True, preload=cell_preload())


# math mode -> verifier function. params (the spec body) is passed straight in.
_MATH_MODES = {
    "equality": _math.verify_equality,
    "inequality": _math.verify_inequality,
    "derivative": _math.verify_derivative,
    "integral": _math.verify_integral,
    "limit": _math.verify_limit,
    "solve": _math.verify_solve,
    "calc_chain": _math.verify_calc_chain,        # grade a worked solution (incl. GSM8K <<expr=result>>)
    "numeric": _math.verify_numeric,              # evaluate an expression, check a claimed value
    "number_theory": _math.verify_number_theory,  # gcd / lcm / primality / factorial / binomial / modulo
    "system": _math.verify_system,                # a claimed solution to a system, by substitution
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
        _log.warning("verify timed out (>%.0fs) mode=%s — shed to ERROR (errs safe, never a false HOLDS)",
                     _VERIFY_TIMEOUT_S, mode)
        return {"status": "ERROR", "detail": f"verification timed out (> {_VERIFY_TIMEOUT_S}s)"}
    except _Saturated:
        _log.warning("verify pool saturated mode=%s — shed to ERROR (errs safe)", mode)
        return {"status": "ERROR", "detail": "verifier busy (too many concurrent verifications) — retry shortly"}
    except _NotCheckable as refused:
        _log.warning("power floor refused mode=%s — reads as not checkable", mode)
        return {"status": "NOT_APPLICABLE", "detail": f"not checkable: {refused}"}
    return {"status": res.status, "detail": (res.detail or "")[:300], "data": dict(res.data or {})}


def _reduce_domain_results(results: List[Any]) -> Dict[str, str]:
    """Reduce a domain's list of VerifierResult to ONE moat status. A contradiction is the
    cardinal signal, so MISMATCH wins over ERROR wins over CONFIRMED; only an all-CONFIRMED
    applicable set is CONFIRMED. No applicable verifier -> NOT_APPLICABLE (an honest gap, an
    INCOMPLETE composite — never a false HOLDS). Mirrors test_fp_gate._status exactly."""
    applicable = [r for r in results if r.applicable]
    if not applicable:
        return {"status": "NOT_APPLICABLE",
                "detail": "no applicable secular verifier for this domain/artifact"}
    # merged verifier outputs, so a later step can BIND to a confirmed prior result (3b). Only ever read
    # for a CONFIRMED source (verify_derivation gates that), so merging all applicable data is harmless.
    merged: Dict[str, Any] = {}
    for r in applicable:
        if getattr(r, "data", None):
            merged.update(r.data)
    mism = [r for r in applicable if r.status == "MISMATCH"]
    if mism:
        return {"status": "MISMATCH", "detail": "; ".join(f"{r.name}: {r.detail}" for r in mism)[:300],
                "data": merged}
    errs = [r for r in applicable if r.status == "ERROR"]
    if errs:
        return {"status": "ERROR", "detail": "; ".join(f"{r.name}: {r.detail}" for r in errs)[:300],
                "data": merged}
    return {"status": "CONFIRMED",
            "detail": "; ".join(f"{r.name}: {r.detail}" for r in applicable if r.passed)[:300],
            "data": merged}


def _read_domain(domain: str, packet: Dict[str, Any]) -> List[Any]:
    """One domain's read, by name, so a cell can be told which function to run."""
    return _verifiers.run_for_domain(domain, packet, surface="secular")


def verify_domain(domain: str, spec: Dict[str, Any]) -> Dict[str, str]:
    """Route a non-math domain claim to its deterministic fleet verifier(s) via
    run_for_domain, on the SECULAR surface only. Same DoS bounds as the math path (size guard
    + shared bounded pool + wall-clock timeout). The FP gate proves 0 false-positives across
    every domain this reaches, so a CONFIRMED here is as trustworthy as a math CONFIRMED."""
    packet = spec or {}
    if len(json.dumps(packet, default=str)) > _MAX_SPEC_CHARS:  # DoS guard, before any verifier
        return {"status": "ERROR", "detail": f"packet too large (> {_MAX_SPEC_CHARS} chars)"}
    try:
        results = _call_with_timeout(_read_domain, domain, packet)
    except _futures.TimeoutError:
        _log.warning("verify timed out (>%.0fs) domain=%s — shed to ERROR (errs safe, never a false HOLDS)",
                     _VERIFY_TIMEOUT_S, domain)
        return {"status": "ERROR", "detail": f"verification timed out (> {_VERIFY_TIMEOUT_S}s)"}
    except _Saturated:
        _log.warning("verify pool saturated domain=%s — shed to ERROR (errs safe)", domain)
        return {"status": "ERROR", "detail": "verifier busy (too many concurrent verifications) — retry shortly"}
    except _NotCheckable as refused:
        _log.warning("power floor refused domain=%s — reads as not checkable", domain)
        return {"status": "NOT_APPLICABLE", "detail": f"not checkable: {refused}"}
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
    except Exception as exc:  # noqa: BLE001 — fail closed; a raise inside a cell names its own type
        return {"status": "ERROR", "detail": f"verifier raised: {getattr(exc, 'kind', type(exc).__name__)}: {str(exc)[:200]}"}


def verify_derivation(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify an ordered derivation. The full trail is always returned; the COMPOSITE verdict
    reports the most serious thing that happened, and `broken_at` / `error_at` / `gap_at` each
    name the FIRST step of their kind — where trust stopped, and why.

    "Our engine could not check this" is NOT "your claim is false." Those are different
    sentences about different things, and only one of them is about the caller. A verifier
    that ERRORs — unusable input, a raise, a missing domain — is a failure of OURS, so it
    returns SYSTEM_ERROR, never BROKEN (contract §5.6, and the taxonomy in §7). Collapsing
    them would be the inverse of the kernel's fifth clause: instead of silently upgrading our
    authority, we would be silently downgrading the caller's claim on the strength of our own
    bug. Someone checking a dosage deserves to know which of the two happened.

    Precedence, so honesty runs BOTH ways:
        BROKEN > SYSTEM_ERROR > INCOMPLETE > HOLDS
    A genuine MISMATCH anywhere still governs — an engine error elsewhere in the derivation
    must not become a place for a real falsehood to hide.
    """
    if not isinstance(steps, list) or not steps:
        return {"verdict": "SYSTEM_ERROR", "detail": "no steps provided", "trail": [],
                "means": "the engine was given nothing to check — this says nothing about any claim"}

    trail: List[Dict[str, Any]] = []
    seen_ids: set = set()
    confirmed_ids: set = set()
    outcome_by_id: Dict[str, str] = {}   # sid -> effective outcome (CONFIRMED|BROKEN|ERROR|GAP)
    domain_by_id: Dict[str, str] = {}    # sid -> domain, so a cross-domain `uses` edge can be gated
    data_by_id: Dict[str, Dict[str, Any]] = {}  # sid -> a CONFIRMED step's verifier outputs, for value-binding
    broken_at = None
    gap_at = None
    error_at = None

    def _worst_dep_outcome(dep_ids: List[str]) -> str:
        # A step confirmed in isolation but standing on unconfirmed ground inherits the WORST of
        # what it stands on — but our-failure (ERROR) and a gap (NOT_APPLICABLE / a missing ref)
        # must NEVER be manufactured into BROKEN. Only a genuine MISMATCH below carries a break up.
        sev = {"BROKEN": 3, "ERROR": 2, "GAP": 1, "CONFIRMED": 0}
        worst, wv = "GAP", 1
        for u in dep_ids:
            o = outcome_by_id.get(u, "GAP")   # a missing/unseen ref -> cannot evaluate -> GAP
            if sev.get(o, 1) > wv:
                worst, wv = o, sev[o]
        return worst if worst != "CONFIRMED" else "GAP"

    for i, step in enumerate(steps):
        sid = str(step.get("id") or f"s{i}")
        domain = str(step.get("domain", ""))
        spec = step.get("spec") or {}
        uses = [str(u) for u in (step.get("uses") or [])]

        # VALUE-BINDING (3b): a step may BUILD an input from a CONFIRMED prior step's output —
        # bind = {"<spec path>": "<srcId>.<outputKey>"} (outputKey defaults to "actual"). A bind IS a
        # dependency, so its source joins `uses`. Fail-closed: if the source is not confirmed or the
        # output key is absent, the binding is UNRESOLVED and the step is NOT verified with a fabricated
        # value — it becomes a GAP, never a guessed HOLDS and never a MISMATCH manufactured from our own
        # inability to resolve a ref. Substitution is into a deep copy, so the caller's spec is never
        # mutated and the spec_hash below binds the seal to exactly what was checked.
        bind = step.get("bind")
        unresolved: List[str] = []
        if isinstance(bind, dict) and bind:
            spec = copy.deepcopy(spec)
            for path, ref in bind.items():
                src_id, _, key = str(ref).partition(".")
                key = key or "actual"
                if src_id not in uses:
                    uses.append(src_id)
                src_data = data_by_id.get(src_id)
                if src_id not in confirmed_ids or not isinstance(src_data, dict) or key not in src_data:
                    unresolved.append("%s<-%s" % (path, ref))
                    continue
                _set_spec_path(spec, str(path), src_data[key])

        missing = [u for u in uses if u not in seen_ids]
        unconfirmed = [u for u in uses if u in seen_ids and u not in confirmed_ids]
        link_ok = not missing and not unconfirmed and not unresolved

        if unresolved:
            # the step could not be BUILT — we cannot check what we could not assemble. A gap, never a
            # false verdict; the dependency gating below still records what it stood on.
            sr: Dict[str, Any] = {"status": "NOT_APPLICABLE",
                                  "detail": "unresolved binding(s): " + ", ".join(unresolved), "data": {}}
        else:
            sr = verify_step(domain, spec)
        st = sr["status"]

        entry: Dict[str, Any] = {
            "id": sid, "domain": domain, "claim": str(step.get("claim", "")),
            "uses": uses, "status": st, "detail": sr.get("detail", ""), "link_ok": link_ok,
            # the fingerprint of exactly what was checked — travels into the seal so the verdict is bound
            # to its artifact, not the free-text label. For a bound step this is the SUBSTITUTED spec, so
            # the seal binds to what was actually verified.
            "spec_hash": _spec_hash(spec),
        }
        # Kind B — surface a verifier's framing (explanation + the question that would let us
        # calculate) so a decline is actionable, not a dead end. Only the curated framing fields
        # travel out, never the verifier's whole internal data dict.
        _g = sr.get("data") or {}
        _framing = {k: _g[k] for k in ("framing_question", "need", "example", "route") if k in _g}
        if _framing:
            entry["guidance"] = _framing
        # the one internal-data field that DOES travel: a typed, independently re-checkable certificate —
        # a witness anyone can re-verify without trusting this engine — carried into the trail and the seal.
        if isinstance(_g.get("certificate"), dict):
            entry["certificate"] = _g["certificate"]
        if missing:
            entry["missing_refs"] = missing
        if unconfirmed:
            entry["builds_on_unconfirmed"] = unconfirmed
        if unresolved:
            entry["unresolved_binding"] = unresolved
        trail.append(entry)
        seen_ids.add(sid)
        domain_by_id[sid] = domain

        # Classify this step's EFFECTIVE outcome. A step that builds on unconfirmed ground cannot
        # stand — but WHY its ground is unconfirmed decides the honest verdict. Collapsing "our
        # engine failed on a step you depend on" (ERROR) or "we had no verifier for it" (gap) into
        # BROKEN would downgrade the caller's claim on the strength of our own failure — the very
        # inversion of the kernel's fifth clause. Only a genuine MISMATCH may propagate a break.
        if st == "MISMATCH":
            outcome = "BROKEN"
        elif st == "ERROR":
            outcome = "ERROR"             # our failure, never the caller's falsehood
        elif st == "NOT_APPLICABLE":
            outcome = "GAP"               # no verifier applied — a gap, never a falsehood
        elif st == "CONFIRMED":
            outcome = "CONFIRMED" if link_ok else _worst_dep_outcome(uses)
        else:
            outcome = "ERROR"             # unknown status = our failure, never the caller's

        # THE SEAM — a cross-domain BRIDGE (registry §4). A step that CONSUMES a step from another
        # domain must not launder rigor across the boundary: a p-value asserted as PROOF, a scaling
        # law with no dimensional analysis. The single-domain verifier above cannot see the join; this
        # does. A category error at the seam BREAKS; a crossing whose justification is absent is a GAP
        # (unproven, never a false HOLDS). Only checked on a genuine cross-domain `uses` edge.
        for u in uses:
            dep_dom = domain_by_id.get(u)
            if not dep_dom or dep_dom == domain:
                continue
            bres = _bridges.check(domain, step, dep_dom)
            bst = bres.get("status")
            if bst == "MISMATCH":
                entry["bridge"] = bres
                outcome = "BROKEN"
                break
            if bst == "INCOMPLETE" and outcome == "CONFIRMED":
                entry["bridge"] = bres
                outcome = "GAP"

        outcome_by_id[sid] = outcome
        if outcome == "CONFIRMED":
            confirmed_ids.add(sid)
            data_by_id[sid] = sr.get("data") or {}   # this step's outputs, available to bind downstream
        elif outcome == "BROKEN":
            if broken_at is None:
                broken_at = sid
        elif outcome == "ERROR":
            if error_at is None:
                error_at = sid
        else:  # GAP
            if gap_at is None:
                gap_at = sid

    # Precedence: a real falsehood governs even if our engine also stumbled elsewhere.
    if broken_at is not None:
        verdict = "BROKEN"
    elif error_at is not None:
        verdict = "SYSTEM_ERROR"
    elif gap_at is not None:
        verdict = "INCOMPLETE"
    else:
        verdict = "HOLDS"

    out = {
        "verdict": verdict,
        "steps": len(steps),
        "confirmed_steps": len(confirmed_ids),
        "broken_at": broken_at,
        "gap_at": gap_at,
        "error_at": error_at,
        "trail": trail,
        "note": ("The trail is the trust: each step is machine-verified and may build "
                 "only on confirmed prior steps. The engine verifies a provided "
                 "derivation; it does not generate the answer."),
    }
    if verdict == "SYSTEM_ERROR":
        out["means"] = ("OUR engine could not perform this check — this is a failure on our side "
                        "and says NOTHING about whether the claim is true. Do not read it as a "
                        "refutation.")
    return out


def verify(spec: Dict[str, Any], domain: str = "mathematics") -> Dict[str, Any]:
    """One-claim convenience: the verdict for a single `{mode, params}` spec."""
    return verify_derivation([{"id": "b", "domain": domain, "spec": spec}])
