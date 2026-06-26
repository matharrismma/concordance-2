"""Governance verifier — structural completeness of a decision packet.

Checks that a DECISION_PACKET has the parts a complete proposal needs, that named
witnesses agree with the declared count, that a declared wait window elapsed, and that
the rationale references the decision it justifies. PURELY STRUCTURAL — it judges shape
and consistency, never the substance.

De-laundered from 1.0 (hotspot #5): the 1.0 verifier carried scriptural anchors on each
check (1 Cor 14:40, Mt 18:16, Prov 19:2, Mt 7:16-20) and a "church" domain profile.
Those are doctrinal framing for the .org witness surface — they are NOT in the secular
core. The structural mechanisms are unchanged; scopes are neutral (local/mesh/archived).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import VerifierResult, confirm, error, mismatch, na

_REQUIRED_FIELDS = ["title", "scope", "red_items", "floor_items",
                    "way_path", "execution_steps", "witnesses"]
_VALID_SCOPES = ("local", "mesh", "archived")
_SCOPE_WAIT_WINDOWS = {"local": 3600, "mesh": 86400, "archived": 604800}
_MIN_RED_ITEMS = 1
_MIN_FLOOR_ITEMS = 1
_MIN_WITNESSES = 1
_MIN_EXECUTION_STEPS = 1


def verify_decision_packet_shape(spec: Dict[str, Any]) -> VerifierResult:
    """Structural completeness check for a decision packet (shape, not substance)."""
    name = "governance.decision_packet_shape"
    if not isinstance(spec, dict):
        return error(name, f"DECISION_PACKET must be an object, got {type(spec).__name__}")

    failures: List[str] = []
    for field in _REQUIRED_FIELDS:
        if field not in spec:
            failures.append(f"missing required field: {field}")
            continue
        value = spec[field]
        if value is None or value == "" or value == []:
            failures.append(f"required field is empty: {field}")

    scope = spec.get("scope")
    if scope is not None and scope not in _VALID_SCOPES:
        failures.append(f"scope={scope!r} not in {_VALID_SCOPES}")

    red_items = spec.get("red_items") or []
    if not isinstance(red_items, list):
        failures.append("red_items must be a list of strings")
    elif len(red_items) < _MIN_RED_ITEMS:
        failures.append(f"red_items has {len(red_items)}, need at least {_MIN_RED_ITEMS}")

    floor_items = spec.get("floor_items") or []
    if not isinstance(floor_items, list):
        failures.append("floor_items must be a list of strings")
    elif len(floor_items) < _MIN_FLOOR_ITEMS:
        failures.append(f"floor_items has {len(floor_items)}, need at least {_MIN_FLOOR_ITEMS}")

    witnesses = spec.get("witnesses") or []
    if not isinstance(witnesses, list):
        failures.append("witnesses must be a list of names or roles")
    elif len(witnesses) < _MIN_WITNESSES:
        failures.append(f"witnesses has {len(witnesses)}, need at least {_MIN_WITNESSES}")

    steps = spec.get("execution_steps") or []
    if not isinstance(steps, list):
        failures.append("execution_steps must be a list of strings")
    elif len(steps) < _MIN_EXECUTION_STEPS:
        failures.append(f"execution_steps has {len(steps)}, need at least {_MIN_EXECUTION_STEPS}")

    way_path = spec.get("way_path")
    if way_path is not None and not isinstance(way_path, str):
        failures.append("way_path must be a string describing the chosen path")
    elif isinstance(way_path, str) and len(way_path.strip()) < 10:
        failures.append("way_path is too short to describe the chosen path")

    rule = ("DECISION_PACKET must declare title, scope, red_items, floor_items, "
            "way_path, execution_steps, and witnesses")
    if failures:
        return mismatch(name, "; ".join(failures), {"rule": rule, "failures": failures})
    return confirm(name,
                   f"complete decision packet: {len(red_items)} red, {len(floor_items)} floor, "
                   f"{len(witnesses)} witnesses, {len(steps)} steps",
                   {"rule": rule, "red_count": len(red_items), "floor_count": len(floor_items),
                    "witness_count": len(witnesses), "step_count": len(steps)})


def verify_witness_count_consistency(spec: Dict[str, Any], packet: Dict[str, Any]) -> VerifierResult:
    """If both DECISION_PACKET.witnesses and top-level witness_count exist, they must agree."""
    name = "governance.witness_count_consistency"
    dp_witnesses = spec.get("witnesses")
    top_count = packet.get("witness_count")
    if dp_witnesses is None or top_count is None:
        return na(name)
    if not isinstance(dp_witnesses, list):
        return error(name, "DECISION_PACKET.witnesses is not a list")
    n_named = len(dp_witnesses)
    try:
        n_top = int(top_count)
    except (ValueError, TypeError):
        return error(name, f"witness_count is non-integer: {top_count!r}")
    data = {"rule": "DECISION_PACKET.witnesses count must equal top-level witness_count",
            "named_count": n_named, "declared_count": n_top}
    if n_named == n_top:
        return confirm(name, f"witnesses count ({n_named}) matches witness_count", data)
    return mismatch(name, f"named {n_named} witnesses but witness_count={n_top}", data)


def verify_decision_timing(packet: Dict[str, Any]) -> VerifierResult:
    """The packet's scope wait window must have elapsed between created and acted."""
    name = "governance.decision_timing"
    scope = (packet.get("scope") or "").lower().strip()
    created = packet.get("created_epoch")
    acted = packet.get("acted_at_epoch")
    if not scope or created is None:
        return na(name, "scope or created_epoch missing")
    if acted is None:
        return na(name, "no acted_at_epoch — cannot judge wait window yet")
    try:
        c, a = int(created), int(acted)
    except (TypeError, ValueError):
        return error(name, "created_epoch/acted_at_epoch must be integers")
    if scope not in _SCOPE_WAIT_WINDOWS:
        return error(name, f"unknown scope {scope!r}; expected local/mesh/archived")
    floor = _SCOPE_WAIT_WINDOWS[scope]
    override = packet.get("wait_window_seconds")
    if override is not None:
        try:
            floor = max(floor, int(override))
        except (TypeError, ValueError):
            return error(name, "wait_window_seconds must be an integer")
    elapsed = a - c
    data = {"rule": "scope-determined wait window must elapse between created and acted",
            "scope": scope, "elapsed_seconds": elapsed, "required_seconds": floor}
    if elapsed < 0:
        return mismatch(name, f"acted before created (elapsed={elapsed}s)", data)
    if elapsed >= floor:
        return confirm(name, f"scope={scope} wait satisfied: {elapsed}s >= {floor}s", data)
    return mismatch(name, f"scope={scope} wait NOT satisfied: {elapsed}s < {floor}s", data)


def verify_rationale_alignment(spec: Dict[str, Any]) -> VerifierResult:
    """Token-overlap check between rationale and decision — catches pasted-rationale fraud."""
    name = "governance.rationale_alignment"
    decision = spec.get("decision")
    rationale = spec.get("rationale")
    if not decision or not rationale:
        return na(name, "decision or rationale missing")
    dec_tokens = set(re.findall(r"[A-Za-z]{4,}", str(decision).lower()))
    rat_text = str(rationale).lower()
    if not dec_tokens:
        return na(name, "decision has no substantive tokens (>=4 chars)")
    matched = [t for t in dec_tokens if t in rat_text]
    rule = "rationale must reference the decision it justifies"
    if matched:
        return confirm(name, f"rationale references decision (overlap: {sorted(matched)[:6]})",
                       {"rule": rule, "matched_tokens": sorted(matched)})
    return mismatch(name, f"rationale shares no >=4-char tokens with decision "
                    f"(decision tokens: {sorted(dec_tokens)[:6]})",
                    {"rule": rule, "decision_tokens": sorted(dec_tokens)})


_DOMAIN_PROFILES = {
    "governance": {"required": [], "recommended": []},
    "business": {"required": ["officers", "fiduciary_basis"],
                 "recommended": ["dollar_amount", "risk_assessment"]},
    "household": {"required": ["budget_category", "affected_dependents"],
                  "recommended": ["time_horizon", "alternatives_considered"]},
    "education": {"required": ["affected_cohort", "learning_objective"],
                  "recommended": ["accommodation_plan", "policy_reference"]},
}


def verify_domain_profile(domain, decision_packet) -> VerifierResult:
    """Verify a decision packet against a per-domain required-field profile."""
    name = "governance.domain_profile"
    domain_key = (domain or "").lower()
    profile = _DOMAIN_PROFILES.get(domain_key)
    if profile is None:
        return na(name, f"no profile registered for domain {domain!r}")
    if not isinstance(decision_packet, dict):
        return error(name, "decision_packet must be an object")
    missing_required = [k for k in profile["required"]
                        if k not in decision_packet or decision_packet[k] in (None, "", [], {})]
    missing_recommended = [k for k in profile["recommended"] if k not in decision_packet]
    data = {"domain": domain_key, "missing_required": missing_required,
            "missing_recommended": missing_recommended}
    if missing_required:
        return mismatch(name, f"{domain} packet missing required: {missing_required}", data)
    if missing_recommended:
        return confirm(name, f"{domain} required present; recommended missing: {missing_recommended}", data)
    return confirm(name, f"{domain} required + recommended fields all present", data)


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    results: List[VerifierResult] = []
    dp = packet.get("DECISION_PACKET")
    if dp is not None:
        results.append(verify_decision_packet_shape(dp))
        results.append(verify_witness_count_consistency(dp, packet))
        results.append(verify_rationale_alignment(dp))
    if "acted_at_epoch" in packet:
        results.append(verify_decision_timing(packet))
    if not results:
        results.append(na("governance", "no DECISION_PACKET artifact present"))
    return results
