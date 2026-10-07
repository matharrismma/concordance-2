"""Unit-pin the medicine verifier (A2: verifier test-depth, 2026-10-06).

Deterministic clinical ARITHMETIC only (never that a value is safe — the verifier checks the formula):
  BMI 70kg/1.75m = 22.86 (normal); dose 10mg/kg x 70kg = 700mg; eAG = 28.7*A1C - 46.7 (A1C 7.0 -> 154.2);
  MAP = DBP + (SBP-DBP)/3 (120/80 -> 93.33); Cockcroft-Gault eGFR (age60, 70kg, Cr1.0, male) = 77.8.
A wrong claim is caught; a missing field is NOT_APPLICABLE (never a false pass).
"""
from __future__ import annotations

from concordance.verifiers import medicine as M


def test_bmi():
    r = M.verify_bmi({"weight_kg": 70, "height_m": 1.75, "claimed_bmi": 22.86})
    assert r.status == "CONFIRMED"
    assert r.data["classification"] == "normal"
    assert M.verify_bmi({"weight_kg": 70, "height_m": 1.75, "claimed_bmi": 30.0}).status == "MISMATCH"
    assert M.verify_bmi({"weight_kg": 70}).status == "NOT_APPLICABLE"


def test_drug_dosage():
    assert M.verify_drug_dosage({"dose_mg_per_kg": 10, "weight_kg": 70, "claimed_dose_mg": 700}).status == "CONFIRMED"
    assert M.verify_drug_dosage({"dose_mg_per_kg": 10, "weight_kg": 70, "claimed_dose_mg": 500}).status == "MISMATCH"
    assert M.verify_drug_dosage({"dose_mg_per_kg": 10}).status == "NOT_APPLICABLE"


def test_a1c_to_eag():
    assert M.verify_a1c_to_eag({"a1c_pct": 7.0, "claimed_eag_mg_dl": 154.2}).status == "CONFIRMED"
    assert M.verify_a1c_to_eag({"a1c_pct": 7.0, "claimed_eag_mg_dl": 120.0}).status == "MISMATCH"
    assert M.verify_a1c_to_eag({}).status == "NOT_APPLICABLE"


def test_mean_arterial_pressure():
    assert M.verify_map({"systolic": 120, "diastolic": 80, "claimed_map_mmhg": 93.3}).status == "CONFIRMED"
    assert M.verify_map({"systolic": 120, "diastolic": 80, "claimed_map_mmhg": 100.0}).status == "MISMATCH"
    assert M.verify_map({"systolic": 120}).status == "NOT_APPLICABLE"


def test_egfr_cockcroft():
    r = M.verify_egfr_cockcroft({"age_years": 60, "weight_kg": 70, "serum_creatinine": 1.0,
                                 "sex_egfr": "male", "claimed_egfr": 77.8})
    assert r.status == "CONFIRMED"
    assert M.verify_egfr_cockcroft({"age_years": 60, "weight_kg": 70, "serum_creatinine": 1.0,
                                    "sex_egfr": "male", "claimed_egfr": 50.0}).status == "MISMATCH"
