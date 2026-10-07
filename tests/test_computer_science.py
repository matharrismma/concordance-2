"""Unit-pin the computer_science verifier (A2, 2026-10-06). Logic-gate equivalence by truth table:
De Morgan, 'A and B' == 'not (not A or not B)'. A false equivalence claim is caught; missing field NA."""
from __future__ import annotations
from concordance.verifiers import computer_science as CS


def test_logic_gate_equivalence():
    assert CS.verify_logic_gate({"gate_a": "A and B", "gate_b": "not (not A or not B)",
                                 "variables": ["A", "B"], "claimed_equivalent": True}).status == "CONFIRMED"
    # 'A and B' is NOT equivalent to 'A or B'; claiming it is must be caught
    assert CS.verify_logic_gate({"gate_a": "A and B", "gate_b": "A or B",
                                 "variables": ["A", "B"], "claimed_equivalent": True}).status == "MISMATCH"
    assert CS.verify_logic_gate({}).status == "NOT_APPLICABLE"
