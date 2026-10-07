"""Unit-pin the electrical verifier (A2: verifier test-depth, 2026-10-06).

Textbook identities, hand-checked: Ohm's law V=I*R (12 = 2*6); power P=V*I (12*2 = 24);
Kirchhoff's voltage law (sum around a loop = 0). A wrong claim is caught; a missing field is
NOT_APPLICABLE (never a false pass).
"""
from __future__ import annotations

from concordance.verifiers import electrical as E


def test_ohms_law():
    assert E.verify_ohms_law({"voltage_V": 12, "current_A": 2, "resistance_ohm": 6}).status == "CONFIRMED"
    assert E.verify_ohms_law({"voltage_V": 12, "current_A": 2, "resistance_ohm": 10}).status == "MISMATCH"
    assert E.verify_ohms_law({}).status == "NOT_APPLICABLE"


def test_power():
    assert E.verify_power({"voltage_V": 12, "current_A": 2, "power_W_claim": 24}).status == "CONFIRMED"
    assert E.verify_power({"voltage_V": 12, "current_A": 2, "power_W_claim": 50}).status == "MISMATCH"
    assert E.verify_power({}).status == "NOT_APPLICABLE"


def test_kirchhoff_voltage_loop():
    assert E.verify_kirchhoff_voltage_loop({"voltages_in_loop": [12, -6, -6],
                                            "claimed_loop_sum_V": 0}).status == "CONFIRMED"
    assert E.verify_kirchhoff_voltage_loop({"voltages_in_loop": [12, -6, -6],
                                            "claimed_loop_sum_V": 5}).status == "MISMATCH"
    assert E.verify_kirchhoff_voltage_loop({}).status == "NOT_APPLICABLE"
