"""M3 (core, cont.) — thin agent dispatch (Conductor Canon Part II Section 5, M3).

Agents GENERATE; they do not judge. Two paths, both ending at the engine, never at the agent:

  * options() — an agent that proposes a SET (quote variants, schedule slots) never returns freely. The
                COMPLETE set is committed BEFORE any evaluation (candidate_commit hashes it), routed under
                the fixed pre-registered policy, narrowed through the derivation moat, and the full trace
                (losers preserved) is sealed. Commitment-before-evaluation is what makes verification
                shopping structurally impossible.
  * single()  — a single-answer agent returns through the frozen AgentReturn contract; its work order then
                validates through the standard gate pipeline and seals. The agent touches neither the gates
                nor the ledger.

It rebuilds nothing: options() composes concordance.candidates; single() composes engine_bridge.gate_and_seal.
The agents themselves (quote, schedule, tooling-check, ...) are authored WITH the shop, not invented here.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from .contracts import AgentReturn, WorkOrder
from . import engine_bridge as _bridge

_STATES = ("SUCCESS", "FAILURE_WITH_HARVEST", "LOSS")


def options(query: str, candidates: List[Union[str, Dict[str, Any]]], *, generator: str,
            generation_method: str = "direct", config=None) -> Dict[str, Any]:
    """Route an option-generating agent through the Candidate Engine. Returns the preserved set + the
    sealed narrowing receipt. No free return: the set is committed before it is evaluated."""
    from concordance import candidates as _C
    cset = _C.create_set(str(query), list(candidates), generator=str(generator),
                         generation_method=str(generation_method))
    _C.commit(cset)        # hash the COMPLETE set before any evaluation — no selective disclosure after
    _C.route(cset)         # fixed, pre-registered routing policy — never the caller's choice
    _C.narrow(cset, config)
    receipt = _C.receipt(cset, config)
    return {
        "candidate_set_id": cset["candidate_set_id"],
        "candidates": [dict(c) for c in cset["candidates"]],      # all preserved, losers included
        "receipt": {"content_hash": receipt.get("content_hash"), "sealed": receipt.get("sealed"),
                    "cite_url": receipt.get("cite_url"), "seal_error": receipt.get("seal_error")},
        "note": "the complete set was committed before evaluation; verification shopping is structurally impossible",
    }


def single(agent_return: AgentReturn, work_order: WorkOrder, *, config=None,
           ledger_dir=None) -> Dict[str, Any]:
    """A single-answer agent returns through the frozen AgentReturn contract; its work order then validates
    through the gate and seals. The agent never touches the gates or the ledger."""
    if not isinstance(agent_return, AgentReturn):
        raise TypeError("single() takes a frozen AgentReturn (an agent never touches the gates or ledger)")
    if agent_return.state not in _STATES:
        raise ValueError("AgentReturn.state must be one of %s" % (_STATES,))
    if not isinstance(work_order, WorkOrder):
        raise TypeError("work_order must be a WorkOrder")
    sealed = _bridge.gate_and_seal(work_order, config=config, ledger_dir=ledger_dir)
    return {"agent_state": agent_return.state, "overall": sealed.overall, "work_type": sealed.work_type,
            "sealed": sealed.ledger_path, "harvest": dict(agent_return.harvest)}
