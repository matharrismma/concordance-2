"""Frozen interfaces (Conductor Canon Part II §3). FROZEN AT M0 — never moved after.

Moving one of these is not a convenience; it is an SOP-12 structural decision (a sealed failure
packet, two witnesses, a 30-day wait). The CI check in tests/test_conductor_m0.py asserts these
field sets do not drift. Redesign is bounded to a failing component; interfaces stay put.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class WorkOrder:
    """What arrives at the panel. `target` carries the costing/measurement inputs an agent needs."""
    request: str
    target: dict = field(default_factory=dict)
    shop_id: str = ""
    order_id: str = ""
    witnesses: tuple = ()          # named human witnesses present (WITNESS gate input)
    timing_clear: bool = True      # WAIT gate hint


@dataclass(frozen=True)
class AgentReturn:
    """An agent takes a target dict and returns exactly this. Never touches the ledger or the gates."""
    state: str                     # SUCCESS | FAILURE_WITH_HARVEST | LOSS
    payload: dict = field(default_factory=dict)
    harvest: dict = field(default_factory=dict)


@dataclass(frozen=True)
class GateResult:
    """The engine's verdict lattice, surfaced to the panel. overall ∈ PASS | REJECT | QUARANTINE."""
    overall: str
    verdicts: tuple = ()           # ((gate, status, reason), ...) from the kernel's gate trail
    tripped: Optional[str] = None  # first non-PASS gate, or None


@dataclass(frozen=True)
class SealedPacket:
    """The result of running a work order through the engine gates and (on PASS) the chain."""
    kind: str                      # SUCCESS | FAILURE
    work_type: str
    overall: str
    summary: str
    ledger_path: Optional[str] = None   # where it sealed in the chain; None unless the record PASSed


# The frozen public surface. CI asserts each name maps to exactly these fields, in order.
FROZEN = {
    "WorkOrder": ("request", "target", "shop_id", "order_id", "witnesses", "timing_clear"),
    "AgentReturn": ("state", "payload", "harvest"),
    "GateResult": ("overall", "verdicts", "tripped"),
    "SealedPacket": ("kind", "work_type", "overall", "summary", "ledger_path"),
}
