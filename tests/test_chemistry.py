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


def _st(spec):
    return [r.status for r in C.run({"CHEM_VERIFY": spec})]


def test_name_to_formula_by_atom_count():
    # 2026-10-12: "water is H2O" and equivalents (C2H5OH == C2H6O), aliases resolved, wrong -> mismatch
    assert _st({"name": "water", "claimed_formula": "H2O"}) == ["CONFIRMED"]
    assert _st({"name": "ethanol", "claimed_formula": "C2H5OH"}) == ["CONFIRMED"]
    assert _st({"name": "salt", "claimed_formula": "NaCl"}) == ["CONFIRMED"]        # alias
    assert _st({"name": "water", "claimed_formula": "CO2"}) == ["MISMATCH"]
    assert _st({"name": "foobar", "claimed_formula": "H2O"}) == ["NOT_APPLICABLE"]  # unknown declined


def test_enantiomeric_excess():
    # 2026-10-13: ee = |R-S|/(R+S)*100%. 99:1 -> 98% ee; racemic 50:50 -> 0%; R+S=0 declined.
    assert _st({"r": 99, "s": 1, "claimed_ee_percent": 98}) == ["CONFIRMED"]
    assert _st({"r": 50, "s": 50, "claimed_ee_percent": 0}) == ["CONFIRMED"]
    assert _st({"r": 99, "s": 1, "claimed_ee_percent": 50}) == ["MISMATCH"]
    assert _st({"r": 0, "s": 0, "claimed_ee_percent": 0}) == ["ERROR"]              # no enantiomers
    assert C.verify_enantiomeric_excess({"claimed_ee_percent": 50}).status == "NOT_APPLICABLE"


def test_chiral_amplification_kagan_soai():
    # 2026-10-13: the Nobel 2026 signature — product ee EXCEEDS seed ee (positive non-linear effect).
    assert _st({"seed_ee_percent": 5, "product_ee_percent": 95,
                "claimed_amplification": True}) == ["CONFIRMED"]                     # Soai-like run-up
    assert _st({"seed_ee_percent": 40, "product_ee_percent": 40,
                "claimed_amplification": False}) == ["CONFIRMED"]                    # no amplification
    assert _st({"seed_ee_percent": 40, "product_ee_percent": 20,
                "claimed_amplification": True}) == ["MISMATCH"]                      # ee dropped, not amplified
    assert _st({"seed_ee_percent": 150, "product_ee_percent": 95,
                "claimed_amplification": True}) == ["ERROR"]                         # ee out of [0,100]
    assert C.verify_chiral_amplification({"seed_ee_percent": 5}).status == "NOT_APPLICABLE"


def test_phase_points_judged_at_stated_precision():
    assert _st({"substance": "water", "property": "boiling", "claimed_c": 100, "claimed_literal": "100"}) == ["CONFIRMED"]
    assert _st({"substance": "water", "property": "freezing", "claimed_c": 0, "claimed_literal": "0"}) == ["CONFIRMED"]
    assert _st({"substance": "iron", "property": "melting", "claimed_c": 1538, "claimed_literal": "1538"}) == ["CONFIRMED"]
    assert _st({"substance": "ethanol", "property": "boiling", "claimed_c": 78, "claimed_literal": "78"}) == ["CONFIRMED"]
    assert _st({"substance": "ethanol", "property": "boiling", "claimed_c": 79, "claimed_literal": "79"}) == ["MISMATCH"]
    # sublimes/decomposes -> no standard point at 1 atm -> declined, never a wrong verdict
    assert _st({"substance": "carbon dioxide", "property": "boiling", "claimed_c": -78, "claimed_literal": "-78"}) == ["NOT_APPLICABLE"]


def test_phase_points_accept_source_spread_but_catch_wrong_values():
    # 2026-10-12: ethanol boils at 78.37; sources also give 78.3 — a half-degree is not an error, but
    # 79 and 88.3 are. (A frontdoor fact, "the boiling point of ethanol is 78.3 C", must hold.)
    assert _st({"substance": "ethanol", "property": "boiling", "claimed_c": 78.3, "claimed_literal": "78.3"}) == ["CONFIRMED"]
    assert _st({"substance": "ethanol", "property": "boiling", "claimed_c": 88.3, "claimed_literal": "88.3"}) == ["MISMATCH"]
    assert _st({"substance": "ethanol", "property": "boiling", "claimed_c": 79, "claimed_literal": "79"}) == ["MISMATCH"]
