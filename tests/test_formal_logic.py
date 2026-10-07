"""Unit-pin the formal_logic verifier (A2, 2026-10-06). 'A or not A' is a tautology (law of excluded
middle). A false tautology claim is caught; a missing field is NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import formal_logic as FL


def test_tautology():
    assert FL.verify_tautology({"formula": "A or not A", "variables": ["A"], "claimed_tautology": True}).status == "CONFIRMED"
    assert FL.verify_tautology({"formula": "A or not A", "variables": ["A"], "claimed_tautology": False}).status == "MISMATCH"
    assert FL.verify_tautology({}).status == "NOT_APPLICABLE"
