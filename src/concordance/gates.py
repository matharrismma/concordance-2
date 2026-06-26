"""Gate verdict constructors.

The gates are the engine's admission checks. The *logic* of each gate lives in
engine.py; these are the three verdict constructors every gate returns.

Gate names (secular core): RED (malformed/contradicted input), FLOOR (protective
domain rules), PATH (among lawful options, the non-coercive one), and an optional
wait/witness step. The witness surface (.org) may surface additional naming, but
the constructors are neutral. Ported as-is from 1.0.
"""
from __future__ import annotations

from typing import Any, Dict

from .packet import GateResult


def reject(gate: str, *reasons: str, details: Dict[str, Any] | None = None) -> GateResult:
    return GateResult(gate=gate, status="REJECT", reasons=list(reasons), details=details)


def quarantine(gate: str, *reasons: str, details: Dict[str, Any] | None = None) -> GateResult:
    return GateResult(gate=gate, status="QUARANTINE", reasons=list(reasons), details=details)


def ok(gate: str, details: Dict[str, Any] | None = None) -> GateResult:
    return GateResult(gate=gate, status="PASS", reasons=[], details=details)
