"""M3 (core) — the Chain executor: thin dispatch, strict walk (Conductor Canon Part II Section 5, M3).

A Chain is an ordered graph of steps; each step is a WorkOrder plus verdict-keyed edges. The executor
walks it one step at a time THROUGH THE ENGINE: each step runs the standard gate pipeline
(engine_bridge.gate_and_seal -> the kernel's RED/FLOOR/PATH/WITNESS/WAIT and, on PASS, the hash-chained
ledger), and the walk advances ONLY on the edge the verdict selects. Three invariants, from the Canon:

  * cannot SKIP            — movement is only along an edge the step's verdict selects;
  * cannot advance UNSIGNED — a step whose work order carries no witness halts the walk;
  * the full walked path is sealed — every step's sealed record, including the branch taken, is kept.

It rebuilds nothing: it composes WorkOrder + gate_and_seal (M0) and the engine's own ledger. The traveler
template (PO -> ship, with quarantine / MRB / re-quote branches) and the five live agents are authored
WITH the shop owner against his real paper traveler, per the Canon's "not invented" rule — they are not
fabricated here. This is the mechanism those ride on.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .contracts import WorkOrder
from . import engine_bridge as _bridge

_VERDICTS = ("PASS", "REJECT", "QUARANTINE")


def step(name: str, request: str, edges: Dict[str, Optional[str]], *,
         witnesses: tuple = ("shop_owner",), target: Optional[dict] = None,
         shop_id: str = "", order_id: str = "") -> Dict[str, Any]:
    """Build one chain step: a WorkOrder plus edges {verdict: next_step_name_or_None}. An edge key must be
    one of PASS / REJECT / QUARANTINE; a verdict with no edge ends the branch (a terminal)."""
    bad = set(edges) - set(_VERDICTS)
    if bad:
        raise ValueError("edge keys must be verdicts %s; got unknown %s" % (_VERDICTS, sorted(bad)))
    tgt = dict(target or {})
    # A step reaches the executor when its turn comes, i.e. after its deliberate WAIT window has elapsed.
    # Default created_epoch to a past time so a ready step is not quarantined by the WAIT gate; override
    # target["created_epoch"] with a recent time to exercise the WAIT gate (a fresh order quarantines).
    tgt.setdefault("created_epoch", 1_700_000_000)
    wo = WorkOrder(request=request, target=tgt, shop_id=shop_id,
                   order_id=order_id, witnesses=tuple(witnesses))
    return {"name": name, "work_order": wo, "edges": dict(edges)}


def walk(chain: Dict[str, Dict[str, Any]], start: str, *, config=None, ledger_dir=None,
         max_steps: int = 64) -> Dict[str, Any]:
    """Walk the chain from `start`, one gated step at a time. Returns the sealed walked path and a status.

    status is one of: "complete" (reached a terminal), "halted_unsigned" (a step had no witness),
    "halted_no_step" (an edge pointed at a missing step), or "halted_max_steps".
    """
    path: List[Dict[str, Any]] = []
    cur: Optional[str] = start
    for _ in range(max_steps):
        if cur is None:
            return _done(path, "complete")
        node = chain.get(cur)
        if node is None:
            path.append({"step": cur, "halted": "NO_SUCH_STEP"})
            return _done(path, "halted_no_step")
        wo: WorkOrder = node["work_order"]
        if not wo.witnesses:                       # cannot advance UNSIGNED
            path.append({"step": cur, "halted": "UNSIGNED — no witness on the work order; "
                                                 "a chain step cannot advance unsigned"})
            return _done(path, "halted_unsigned")
        sealed = _bridge.gate_and_seal(wo, config=config, ledger_dir=ledger_dir)
        edges = node.get("edges") or {}
        nxt = edges.get(sealed.overall)            # advance ONLY on the matching edge
        path.append({"step": cur, "verdict": sealed.overall, "sealed": sealed.ledger_path,
                     "work_type": sealed.work_type, "next": nxt})
        if sealed.overall not in edges:            # no edge for this verdict -> terminal (branch ends)
            return _done(path, "complete")
        cur = nxt
    return _done(path, "halted_max_steps")


def _done(path: List[Dict[str, Any]], status: str) -> Dict[str, Any]:
    return {
        "status": status,
        "walked": path,
        "steps": len(path),
        "sealed_path": [p["sealed"] for p in path if p.get("sealed")],
        "note": ("the walk is sealed step by step; it cannot skip (movement is only along a matching edge), "
                 "cannot advance unsigned, and keeps the full path including the branch taken"),
    }
