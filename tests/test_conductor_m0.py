"""Conductor M0 — Baseline & Wiring Proof.

Exit criteria (Conductor Canon Part II §5, M0): a work order flows capture -> validate_packet ->
chain, end to end, using ONLY existing engine organs; the gates delegate to the deployed kernel; and
contracts.py is frozen with a CI surface check. These tests are that proof.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from conductor.contracts import FROZEN, WorkOrder  # noqa: E402
import conductor.contracts as contracts  # noqa: E402
from conductor.engine_bridge import gate_and_seal, gate_result  # noqa: E402
from concordance.ledger import verify_chain  # noqa: E402

CLEAN = WorkOrder(request="quote 50 brackets at a fair margin, log every step openly",
                  target={"created_epoch": 1000}, shop_id="signal", order_id="4417",
                  witnesses=("shop_owner", "inspector"))
PREDATORY = WorkOrder(request="prey on the vulnerable with fake testimonials and hidden fees",
                      target={"created_epoch": 1000}, shop_id="signal", order_id="X",
                      witnesses=("shop_owner", "inspector"))
ELAPSED = 1000 + 10 ** 9   # now_epoch far enough past created that the WAIT window has elapsed


# ---- THE M0 EXIT: capture -> gates -> chain, existing organs only ----

def test_a_work_order_flows_end_to_end_to_the_chain():
    with tempfile.TemporaryDirectory() as tmp:
        ld = Path(tmp) / "ledger"
        sealed = gate_and_seal(CLEAN, now_epoch=ELAPSED, ledger_dir=ld)
        assert sealed.overall == "PASS", f"clean order should pass once its WAIT window elapsed, got {sealed.overall}"
        assert sealed.kind == "SUCCESS"
        assert sealed.ledger_path is not None, "a PASS record must seal to the chain"
        assert Path(sealed.ledger_path).exists()
        assert verify_chain(ledger_dir=ld)["ok"] is True, "the sealed chain must verify"


# ---- the engine's gates genuinely govern (delegation is real, not cosmetic) ----

def test_predatory_plan_is_rejected_by_RED_and_never_seals():
    with tempfile.TemporaryDirectory() as tmp:
        ld = Path(tmp) / "ledger"
        sealed = gate_and_seal(PREDATORY, now_epoch=ELAPSED, ledger_dir=ld)
        assert sealed.overall == "REJECT"
        assert sealed.kind == "FAILURE"
        assert sealed.ledger_path is None, "a rejected plan must NOT seal to the chain"
    gr = gate_result(PREDATORY, now_epoch=ELAPSED)
    assert gr.tripped == "RED", f"the moral scan should trip RED, tripped {gr.tripped}"


def test_order_inside_its_wait_window_quarantines_and_does_not_seal():
    with tempfile.TemporaryDirectory() as tmp:
        ld = Path(tmp) / "ledger"
        # now_epoch == created -> zero elapsed -> WAIT quarantines
        sealed = gate_and_seal(CLEAN, now_epoch=1000, ledger_dir=ld)
        assert sealed.overall == "QUARANTINE"
        assert sealed.ledger_path is None
    gr = gate_result(CLEAN, now_epoch=1000)
    assert gr.tripped == "WAIT"


def test_gate_result_carries_the_full_trail():
    gr = gate_result(CLEAN, now_epoch=ELAPSED)
    # the kernel's five-gate spine ran, in order (a gate may contribute several sub-checks)
    seen = []
    for gate, _status, _reason in gr.verdicts:
        if gate not in seen:
            seen.append(gate)
    assert seen == ["RED", "FLOOR", "PATH", "WITNESS", "WAIT"], seen
    assert gr.overall == "PASS" and gr.tripped is None


# ---- contracts.py is FROZEN (the CI surface check) ----

def test_frozen_interfaces_have_not_drifted():
    import dataclasses
    for name, expected in FROZEN.items():
        cls = getattr(contracts, name)
        actual = tuple(f.name for f in dataclasses.fields(cls))
        assert actual == expected, f"{name} interface drifted: {actual} != {expected} (SOP-12 required to move it)"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
