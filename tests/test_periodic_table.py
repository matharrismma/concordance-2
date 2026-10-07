"""Unit-pin the periodic_table verifier (A2, 2026-10-06). Z=1 is H; molar mass of H2O ~ 18.015 g/mol."""
from __future__ import annotations
from concordance.verifiers import periodic_table as PT


def test_element():
    assert PT.verify_element({"atomic_number": 1, "claimed_symbol": "H"}).status == "CONFIRMED"
    assert PT.verify_element({"atomic_number": 1, "claimed_symbol": "He"}).status == "MISMATCH"
    assert PT.verify_element({}).status == "NOT_APPLICABLE"


def test_molar_mass():
    assert PT.verify_molar_mass({"formula": "H2O", "claimed_molar_mass": 18.015}).status == "CONFIRMED"
    assert PT.verify_molar_mass({"formula": "H2O", "claimed_molar_mass": 20.0}).status == "MISMATCH"
