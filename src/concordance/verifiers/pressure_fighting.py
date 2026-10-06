"""THE PRESSURE FIGHTING SYSTEM — the combat grammar, enforced by the engine (Matt, 2026-10-06).

Matt's system (20 years grappling + UFC coaching) produced the engine's own law — found never generated,
closed set, held or not held, honest count, drift. This verifier returns that law to the mat: it enforces
the Canonical Combat Grammar (grammar_v0.2, the author's act, ingested as data/pfs_grammar.json) so an
exchange is classified in a CLOSED SET with a binary verdict, MATCH or NO_MATCH, never a grade. It is the
first link of the chain to optimal: a position stated in grammar values that the downstream tools can walk.

The Red-Team Directive demanded exactly this: a closed-set ontology two coaches apply identically, enforced
in software, deterministic, no model generating anything. This is a port of the author's own validate.py
(observation mode); the grammar is the reference, this is the enforcement. A model may never author a
tactic, a route, or a card — the engine only checks what the author and the film establish.

PFS_VERIFY packet:
  {"observation": {exchange_id, athlete_id, frame_seq, grammar_version, control_target,
                   control_configuration, fight_state, progression_rung, plane_surface,
                   plane_defined_by, outcome, leak, end, candidate}}   -> MATCH / NO_MATCH
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error

_GRAMMAR: Dict[str, Any] = {}
_HASH = ""

_OBS_REQUIRED = ("exchange_id", "athlete_id", "frame_seq", "grammar_version", "control_target",
                 "control_configuration", "fight_state", "progression_rung", "plane_surface",
                 "plane_defined_by", "outcome", "leak", "end", "candidate")


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def _load() -> Dict[str, Any]:
    global _GRAMMAR, _HASH
    if _GRAMMAR:
        return _GRAMMAR
    d = _data_dir()
    try:
        g = json.loads((d / "pfs_grammar.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    _GRAMMAR = g
    h = hashlib.sha256()
    for name in ("pfs_grammar.json", "pfs_card_schema.json"):
        p = d / name
        if p.exists():
            h.update(json.dumps(json.loads(p.read_text(encoding="utf-8")), sort_keys=True,
                                separators=(",", ":")).encode())
    _HASH = h.hexdigest()[:16]
    return _GRAMMAR


def grammar_hash() -> str:
    _load()
    return _HASH


def _enum(dim: str, sub: str = "values"):
    return (_GRAMMAR.get("dimensions", {}).get(dim, {}) or {}).get(sub, [])


def verify_observation(spec: Dict[str, Any]) -> VerifierResult:
    """Classify one frame of an exchange in the closed-set grammar. MATCH if every field is in its closed
    set (unclear permitted only on observables, as the grammar allows) and the candidate/end rules hold;
    NO_MATCH otherwise. Deterministic, no model — the film decides, the grammar names."""
    name = "pressure_fighting.observation"
    g = _load()
    if not g:
        return na(name, "the combat grammar (data/pfs_grammar.json) is not present on this node")
    if not isinstance(spec, dict):
        return error(name, "observation must be an object")
    data = {"grammar_version": g.get("grammar_version"), "grammar_hash": grammar_hash()}
    # unknown / missing fields (additionalProperties: false; all 14 required)
    extra = [k for k in spec if k not in _OBS_REQUIRED]
    if extra:
        return mismatch(name, f"NO_MATCH: unknown field(s) {extra}", data)
    missing = [k for k in _OBS_REQUIRED if k not in spec]
    if missing:
        return mismatch(name, f"NO_MATCH: missing required field(s) {missing}", data)
    # typed non-enum fields
    for sid in ("exchange_id", "athlete_id"):
        if not isinstance(spec[sid], str) or not spec[sid].strip():
            return mismatch(name, f"NO_MATCH: {sid} must be a non-empty string", data)
    if not isinstance(spec["frame_seq"], int) or isinstance(spec["frame_seq"], bool) or spec["frame_seq"] < 1:
        return mismatch(name, "NO_MATCH: frame_seq must be an integer >= 1", data)
    if spec["grammar_version"] != g.get("grammar_version"):
        return mismatch(name, f"NO_MATCH: grammar_version {spec['grammar_version']} != {g.get('grammar_version')}", data)
    if not isinstance(spec["candidate"], bool):
        return mismatch(name, "NO_MATCH: candidate must be a boolean", data)
    # closed-set enums (unclear is included in each observable dimension's value list by the grammar)
    enum_fields = {
        "control_target": _enum("control_target"), "control_configuration": _enum("control_configuration"),
        "fight_state": _enum("fight_state"), "progression_rung": _enum("progression_rung"),
        "plane_surface": _enum("plane", "surface"), "plane_defined_by": _enum("plane", "defined_by"),
        "outcome": _enum("outcome"), "leak": _enum("leak"), "end": _enum("end"),
    }
    for f, allowed in enum_fields.items():
        if spec[f] not in allowed:
            return mismatch(name, f"NO_MATCH: {f}={spec[f]!r} is out of the closed set {allowed}", data)
    # v0.2 candidate rule: a candidate finish is only meaningful BELOW finishing_position
    rung = spec["progression_rung"]
    if spec["candidate"] and rung in ("finishing_position", "finish"):
        return mismatch(name, "NO_MATCH: candidate=true at or above finishing_position is not a candidate", data)
    # v0.2 end rule: a finishing rung must name the end of the rope
    if rung in ("finishing_position", "finish") and spec["end"] == "none":
        return mismatch(name, "NO_MATCH: a finishing rung requires end=head|ankle|unclear", data)
    data.update({k: spec[k] for k in ("control_target", "control_configuration", "fight_state",
                                      "progression_rung", "outcome", "leak", "end", "candidate")})
    return confirm(name, f"MATCH: a valid grammar classification (rung={rung}, state={spec['fight_state']}, "
                         f"target={spec['control_target']}/{spec['control_configuration']})", data)


def verify_card(spec: Dict[str, Any]) -> VerifierResult:
    """Position-card enforcement is the NEXT link (the full position_card schema, held/no_match tests,
    exactly two authored reaction branches, exits, recovery, the evidence floor). Declined here rather
    than half-checked: a partial card validator could pass a bad card, and the engine never false-MATCHes.
    Use the author's validate.py until this link lands."""
    return na("pressure_fighting.card", "card validation is the next link; not enforced here yet (never half-checked)")


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    pv = packet.get("PFS_VERIFY") or {}
    out: List[VerifierResult] = []
    if isinstance(pv, dict) and "observation" in pv:
        out.append(verify_observation(pv["observation"]))
    if isinstance(pv, dict) and "card" in pv:
        out.append(verify_card(pv["card"]))
    if not out:
        out.append(na("pressure_fighting", "no PFS_VERIFY observation present"))
    return out
