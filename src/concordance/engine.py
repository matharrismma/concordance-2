"""The engine — the going train. validate_and_seal: claim -> gates -> verifiers
-> (verdict, trail, seal).

Five gates fire in order:
  RED     — malformed input / a verifier contradicted the claim (hard reject)
  FLOOR   — protective domain rules / attestations (hard reject)
  PATH    — among lawful options, the declared path is non-coercive (was WAY in 1.0;
            renamed for the secular surface — the coercion-keyword mechanism is
            unchanged, the religious framing removed)
  WITNESS — required corroborating witnesses are present (was BROTHERS; quarantine)
  WAIT    — a deliberate wait window has elapsed before sealing (was GOD; quarantine)

RED and FLOOR are HARD gates (reject). PATH can reject. WITNESS and WAIT quarantine.
Ported from 1.0 src/concordance_engine/engine.py — logic faithful, names neutral.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from . import verifiers as _verifiers
from .config import EngineConfig
from .domains import load_domain_validator
from .gates import ok, quarantine, reject
from .packet import DecisionStatus, EngineResult, GateResult
from .record import Anchor, ClosestCase, WitnessRecord, axis_coords_for
from .validate import resolve_schema, validate_against_schema
from .verifiers.base import VerifierResult

# Wait windows by scope (seconds). Neutral scope names (1.0: adapter/mesh/canon).
WAIT_WINDOWS = {
    "local": 60 * 60,
    "mesh": 24 * 60 * 60,
    "archived": 7 * 24 * 60 * 60,
}

HARD_GATES = ("RED", "FLOOR")

# Decision-packet domains: their flat fields get auto-wrapped so the (future)
# governance verifier sees a DECISION_PACKET. Secular set (no "church").
_GOVERNANCE_DOMAINS = {"governance", "business", "household", "education"}
_DP_TRIGGER_FIELDS = ("red_items", "floor_items", "path", "execution_steps", "witnesses")
_DP_ALL_FIELDS = _DP_TRIGGER_FIELDS + ("title", "scope", "wait_window_seconds")

def _get_schema(config: EngineConfig) -> Dict[str, Any] | None:
    """Resolve the schema for validation, or None. The schema ships inside the package
    (validate.DEFAULT_SCHEMA_PATH); a missing one is logged loudly there, not silent."""
    return resolve_schema(config.schema_path)


def _scope_seconds(scope: Optional[str]) -> int:
    return WAIT_WINDOWS.get((scope or "").lower(), WAIT_WINDOWS["local"])


def _normalize_governance_packet(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Auto-wrap flat decision packets so the verifier sees DECISION_PACKET.
    Returns a new dict; does not mutate input. No-op for non-governance domains."""
    domain = (packet.get("domain") or "").lower()
    if domain not in _GOVERNANCE_DOMAINS:
        return packet
    out = dict(packet)
    if "DECISION_PACKET" not in out and any(f in out for f in _DP_TRIGGER_FIELDS):
        out["DECISION_PACKET"] = {f: out[f] for f in _DP_ALL_FIELDS if f in out}
    if "witness_count" not in out:
        wits = out.get("witnesses")
        if wits is None and isinstance(out.get("DECISION_PACKET"), dict):
            wits = out["DECISION_PACKET"].get("witnesses")
        if isinstance(wits, list):
            out["witness_count"] = len(wits)
    return out


# ── PATH gate ────────────────────────────────────────────────────────────
# Among lawful options, the declared path of action must not be openly coercive.
# Mechanical (V1): locate the path field; if absent, the gate is NA (passes with a
# note) — most claims declare no path. If present, scan for coercion keywords;
# a match rejects. Keyword-level only; the substantive judgement stays human.

_PATH_COERCION_KEYWORDS = (
    "force", "compel", "coerce", "mandate", "override",
    "without consent", "regardless of", "ignore objection",
    "silence dissent", "punish disagreement", "demand compliance",
    "enforce by", "make them", "shut down", "make him", "make her",
)


def _check_path_gate(packet: Dict[str, Any]) -> GateResult:
    path: Optional[str] = None
    dp = packet.get("DECISION_PACKET")
    if isinstance(dp, dict):
        path = dp.get("path") or dp.get("way_path")
    if not path:
        path = packet.get("path") or packet.get("way_path") or packet.get("way_check")

    if not path or not isinstance(path, str) or not path.strip():
        return ok("PATH", {"note": "no path declared — PATH check skipped",
                           "rule": "among lawful options, choose the non-coercive path"})

    matched = [kw for kw in _PATH_COERCION_KEYWORDS if kw in path.lower()]
    if matched:
        return reject("PATH", f"path contains coercion keywords: {matched}",
                      details={"path": path, "matched_keywords": matched,
                               "rule": "the chosen path must avoid coercion"})
    return ok("PATH", {"path": path,
                       "rule": "PATH passed: declared, no coercion keywords. The "
                               "substantive judgement remains the human's call."})


def _run_validation(packet: Dict[str, Any], *, now_epoch: Optional[int],
                    config: EngineConfig) -> Tuple[List[GateResult], Tuple[VerifierResult, ...], DecisionStatus]:
    """Run RED -> FLOOR -> PATH -> WITNESS -> WAIT plus verifier dispatch."""
    gate_results: List[GateResult] = []
    verifier_results: List[VerifierResult] = []

    if not config.skip_schema_validation:
        schema = _get_schema(config)
        if schema is not None:
            try:
                validate_against_schema(packet, schema)
            except Exception as e:  # noqa: BLE001 — ValidationError or ValueError
                gate_results.append(reject("RED", f"schema validation failed: {e}",
                                           details={"validation_error": str(e)}))
                return gate_results, tuple(verifier_results), "REJECT"

    packet = _normalize_governance_packet(packet)
    domain = (packet.get("domain") or "").lower()
    dv = load_domain_validator(domain)

    # RED — domain validator (artifact malformed / contradicted)
    if dv:
        gate_results.extend(dv.validate_red(packet))
        if any(gr.status == "REJECT" for gr in gate_results if gr.gate == "RED"):
            return gate_results, tuple(verifier_results), "REJECT"
    else:
        gate_results.append(ok("RED", {"note": "no domain validator registered"}))

    # RED — verifier dispatch (does the math/logic actually hold)
    if config.run_verifiers:
        ver_results = _verifiers.run_for_domain(domain, packet, surface=config.surface)
        verifier_results.extend(ver_results)
        ver_failures = [v for v in ver_results if v.failed]
        ver_passes = [v for v in ver_results if v.passed]
        ver_na = [v for v in ver_results if not v.applicable]
        if ver_failures:
            reasons = [f"{v.name}: {v.detail}" for v in ver_failures]
            gate_results.append(reject("RED", *reasons, details={
                "verifier_failures": [v.__dict__ for v in ver_failures],
                "verifier_passes": [v.__dict__ for v in ver_passes]}))
            return gate_results, tuple(verifier_results), "REJECT"
        if ver_passes:
            gate_results.append(ok("RED", {
                "verified": [f"{v.name}: {v.detail}" for v in ver_passes],
                "not_applicable": [v.name for v in ver_na]}))

    # FLOOR — protective domain attestations
    if dv:
        gate_results.extend(dv.validate_floor(packet))
        if any(gr.status == "REJECT" for gr in gate_results if gr.gate == "FLOOR"):
            return gate_results, tuple(verifier_results), "REJECT"
    else:
        gate_results.append(ok("FLOOR", {"note": "no domain validator registered"}))

    # PATH — non-coercion
    path_result = _check_path_gate(packet)
    gate_results.append(path_result)
    if path_result.status == "REJECT":
        return gate_results, tuple(verifier_results), "REJECT"

    # WITNESS — required corroboration
    required = int(packet.get("required_witnesses") or 0)
    have = int(packet.get("witness_count") or 0)
    if required > 0 and have < required:
        gate_results.append(quarantine("WITNESS", f"witnesses {have}/{required}"))
        return gate_results, tuple(verifier_results), "QUARANTINE"
    gate_results.append(ok("WITNESS", {"witnesses": have, "required": required}))

    # WAIT — a deliberate window before sealing
    scope = packet.get("scope") or config.default_scope
    try:
        packet_wait = int(packet.get("wait_window_seconds") or 0)
    except (TypeError, ValueError):
        packet_wait = 0
    wait_s = max(_scope_seconds(scope), packet_wait)
    created = int(packet.get("created_epoch") or 0)
    if now_epoch is None:
        now_epoch = int(time.time())
    elapsed = max(0, now_epoch - created)
    if created == 0:
        gate_results.append(quarantine("WAIT", "created_epoch missing"))
        return gate_results, tuple(verifier_results), "QUARANTINE"
    if elapsed < wait_s:
        gate_results.append(quarantine("WAIT", f"wait {elapsed}/{wait_s} seconds"))
        return gate_results, tuple(verifier_results), "QUARANTINE"
    gate_results.append(ok("WAIT", {"elapsed": elapsed, "required": wait_s}))

    return gate_results, tuple(verifier_results), "PASS"


def validate_packet(packet: Dict[str, Any], *, now_epoch: Optional[int] = None,
                    config: EngineConfig) -> EngineResult:
    """Run the gates; return overall status + gate trail. For the sealed-record
    shape (verifier results, anchors, coords first-class) use validate_and_seal."""
    gate_results, _vr, overall = _run_validation(packet, now_epoch=now_epoch, config=config)
    return EngineResult(overall=overall, gate_results=gate_results)


def validate_and_seal(packet: Dict[str, Any], *, now_epoch: Optional[int] = None,
                      config: EngineConfig, anchors: Tuple[Anchor, ...] = (),
                      closest_case: Optional[ClosestCase] = None,
                      packet_id: Optional[str] = None) -> WitnessRecord:
    """Run the gates and produce a sealed WitnessRecord — the canonical entry point.

    The record carries every gate verdict, every verifier result, anchors with
    provenance layer, grid coordinates, and an optional precedent overlay — but no
    fabricated answer field. Anchors and closest_case come from the caller (their
    sources live outside the engine)."""
    gate_results, verifier_results, overall = _run_validation(
        packet, now_epoch=now_epoch, config=config)
    domain_raw = packet.get("domain") if isinstance(packet, dict) else None
    domain = domain_raw.lower() if isinstance(domain_raw, str) else ""
    return WitnessRecord(
        overall=overall,
        gate_results=tuple(gate_results),
        verifier_results=verifier_results,
        anchors=tuple(anchors),
        axis_coords=axis_coords_for(domain),
        closest_case=closest_case,
        packet_id=packet_id,
    )
