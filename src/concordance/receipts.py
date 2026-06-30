"""Receipts — mint a re-checkable seal from a verification result.

This is what makes the thesis real. A verdict alone is "trust me"; a SEAL is the
receipt. Given a derivation result (verdict + worked trail), this builds the canonical
WitnessRecord, content-addresses it in the CAS (so anyone can re-fetch and re-verify it),
appends confirmed (PASS/HOLDS) results to the tamper-evident ledger chain, and returns the
seal {content_hash, cite_url}.

HONEST BY CONSTRUCTION: minting is best-effort for availability, but a verdict is NEVER
presented as receipted unless a real, re-fetchable seal was actually stored — on failure the
caller surfaces seal:null + a reason. A receipt you cannot re-check is exactly the "trust me"
this engine exists to defeat.

A receipt is minted for BROKEN verdicts too (proof a claim is false is as valuable as proof
it holds); only PASS results enter the ledger chain (the ledger records resolved precedents).

Sovereign: stdlib + the floor (cas, ledger, record) only.
"""
from __future__ import annotations

import os
import threading
from typing import Any, Dict, Optional

from . import cas, ledger, redact
from .config import EngineConfig
from .packet import GateResult
from .record import WitnessRecord, axis_coords_for, with_permanent_ref
from .verifiers.base import VerifierResult

# verify_derivation verdicts -> the sealed record's DecisionStatus
_VERDICT_TO_OVERALL = {"HOLDS": "PASS", "BROKEN": "REJECT", "INCOMPLETE": "QUARANTINE",
                       "ERROR": "REJECT"}

# Appending to the hash chain is read-then-write; serialize it within the process so
# concurrent /verify requests cannot fork the chain (ThreadingHTTPServer is one process).
_LEDGER_LOCK = threading.Lock()


def _public_base(config: EngineConfig) -> str:
    """The re-checkable base URL for cite_url. Overridable; defaults by surface."""
    env = os.environ.get("CONCORDANCE_PUBLIC_BASE", "").strip()
    if env:
        return env.rstrip("/")
    return "https://narrowhighway.org" if config.surface == "witness" else "https://narrowhighway.com"


def _auto_summary(result: Dict[str, Any], domain: str) -> str:
    claim = ""
    for e in (result.get("trail") or []):
        if e.get("claim"):
            claim = str(e["claim"])
            break
    base = redact.redact(claim)[0] if claim else f"{domain} derivation"  # never seal PII in the summary
    return f"{base} — {result.get('verdict')} ({result.get('confirmed_steps', 0)}/{result.get('steps', 0)} steps)"


def record_from_derivation(result: Dict[str, Any], *, domain: str = "mathematics",
                           packet_id: Optional[str] = None) -> WitnessRecord:
    """Adapt a derivation result (verdict + trail) into the canonical WitnessRecord.

    The trail becomes verifier_results (each step's status carries through, 1:1 with the
    derivation's own statuses), and a single RED gate reflects the composite verdict — so the
    sealed record is a faithful, self-describing snapshot of exactly what was checked."""
    verdict = str(result.get("verdict", "ERROR"))
    overall = _VERDICT_TO_OVERALL.get(verdict, "REJECT")
    trail = result.get("trail") or []
    vrs = tuple(
        VerifierResult(
            name=str(e.get("id") or f"s{i}"),
            status=str(e.get("status") or "ERROR"),
            detail=str(e.get("detail") or ""),
            # redact the human claim text before it enters the permanent, public seal — the
            # seal records the stripped form; the PII never reaches the ledger (math is untouched).
            data={"claim": redact.redact(str(e.get("claim", "")))[0], "domain": e.get("domain", ""),
                  "uses": e.get("uses", []), "link_ok": e.get("link_ok", True)},
        )
        for i, e in enumerate(trail)
    )
    gate = GateResult(
        gate="RED",
        status="PASS" if overall == "PASS" else "REJECT",
        reasons=[f"derivation verdict: {verdict}"],
        details={"verdict": verdict, "steps": result.get("steps"),
                 "confirmed_steps": result.get("confirmed_steps"),
                 "broken_at": result.get("broken_at"), "gap_at": result.get("gap_at")},
    )
    return WitnessRecord(overall=overall, gate_results=(gate,), verifier_results=vrs,
                         axis_coords=axis_coords_for(domain), packet_id=packet_id)


def mint(result: Dict[str, Any], *, config: EngineConfig, domain: str = "mathematics",
         summary: Optional[str] = None, sealed_at: Optional[float] = None) -> Dict[str, Any]:
    """Mint a re-checkable seal for a derivation result.

    Returns {ok: True, content_hash, cite_url, ledgered} on success (the CAS write succeeded
    and the seal is re-fetchable), or {ok: False, error} on failure. Never raises — but never
    lies: ok is True only if a real seal was stored."""
    try:
        record = record_from_derivation(result, domain=domain)
        content_hash = cas.store(record.to_dict())  # content-addressed, idempotent
        ledgered = False
        if record.overall == "PASS":
            axis = record.axis_coords.axis if record.axis_coords else domain
            precedent_id = f"ledger://{axis}/{content_hash[:16]}"  # unique per content
            with _LEDGER_LOCK:
                try:
                    ledger.seal_to_ledger(
                        with_permanent_ref(record, content_hash),
                        summary=(summary or _auto_summary(result, domain))[:200],
                        precedent_id=precedent_id, sealed_at=sealed_at, overwrite=False)
                    ledgered = True
                except FileExistsError:
                    ledgered = True  # identical content already chained — idempotent
                except Exception:  # noqa: BLE001 — ledger append failed; the CAS seal still stands
                    ledgered = False
        return {"ok": True, "content_hash": content_hash, "ledgered": ledgered,
                "cite_url": f"{_public_base(config)}/seal?hash={content_hash}"}
    except Exception as exc:  # noqa: BLE001 — never break a verdict because sealing failed
        return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:160]}"}


def attach(result: Dict[str, Any], *, config: EngineConfig, domain: str = "mathematics",
           enabled: bool = True) -> Dict[str, Any]:
    """Return a copy of `result` with an honest seal attached.

    seal = {content_hash, cite_url, ledgered} when a real seal was stored; seal = null with a
    seal_error when minting was attempted and failed; seal omitted only when disabled."""
    out = dict(result)
    if not enabled:
        return out
    s = mint(result, config=config, domain=domain)
    if s.get("ok"):
        out["seal"] = {"content_hash": s["content_hash"], "cite_url": s["cite_url"],
                       "ledgered": s.get("ledgered", False)}
    else:
        out["seal"] = None
        out["seal_error"] = s.get("error", "seal could not be minted")
    return out
