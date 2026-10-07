"""Unit-pin the chemistry verifier's spec-driven checks (A2: verifier test-depth, 2026-10-06).

pH classification (pH 3 = acid, pH 11 = base) and Gibbs spontaneity (dG = dH - T*dS < 0 =>
spontaneous; dH=-100 kJ/mol, dS=50 J/mol/K, T=298 K => dG ~ -114.9 kJ/mol, spontaneous). A wrong
claim is caught; a missing field is NOT_APPLICABLE (never a false pass).
(The equation-balancer and constant-scale checks are exercised elsewhere; this pins the spec rules.)
"""
from __future__ import annotations

from concordance.verifiers import chemistry as C


def test_ph_classification():
    assert C.verify_ph_classification({"pH": 3.0, "claimed_classification": "acid"}).status == "CONFIRMED"
    assert C.verify_ph_classification({"pH": 11.0, "claimed_classification": "base"}).status == "CONFIRMED"
    assert C.verify_ph_classification({"pH": 3.0, "claimed_classification": "base"}).status == "MISMATCH"
    assert C.verify_ph_classification({}).status == "NOT_APPLICABLE"


def test_thermodynamic_feasibility():
    spont = C.verify_thermodynamic_feasibility({"delta_H_kJ_mol": -100, "delta_S_J_mol_K": 50,
                                                "temperature_K": 298, "claimed_spontaneous": True})
    assert spont.status == "CONFIRMED"
    wrong = C.verify_thermodynamic_feasibility({"delta_H_kJ_mol": -100, "delta_S_J_mol_K": 50,
                                                "temperature_K": 298, "claimed_spontaneous": False})
    assert wrong.status == "MISMATCH"
