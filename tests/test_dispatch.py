"""M3 (core) — thin agent dispatch (conductor/dispatch.py, 2026-10-06). The single-answer path and the
contract guards are pinned here (fast); the option path (candidate engine) is validated live on the node.
A single-answer agent returns through the frozen AgentReturn contract and its work order validates through
the gate; a non-AgentReturn or an unknown state is refused (an agent never touches the gates or ledger).
"""
from __future__ import annotations

import pytest

from conductor import dispatch as D
from conductor.contracts import AgentReturn, WorkOrder


def test_single_validates_through_the_gate(tmp_path):
    wo = WorkOrder(request="quote 20 aluminum brackets to print", target={"created_epoch": 1700000000},
                   witnesses=("owner",))
    r = D.single(AgentReturn(state="SUCCESS", payload={"quote": 100}), wo, ledger_dir=tmp_path)
    assert r["agent_state"] == "SUCCESS"
    assert r["overall"] in ("PASS", "REJECT", "QUARANTINE")   # the gate decides, not the agent


def test_single_refuses_non_agentreturn():
    wo = WorkOrder(request="x", witnesses=("owner",))
    with pytest.raises(TypeError):
        D.single({"state": "SUCCESS"}, wo)


def test_single_refuses_unknown_state():
    wo = WorkOrder(request="x", witnesses=("owner",))
    with pytest.raises(ValueError):
        D.single(AgentReturn(state="MAYBE"), wo)
