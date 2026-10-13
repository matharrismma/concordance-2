"""Unit-pin the quantum_computing verifier (A2, 2026-10-06). A qubit state is normalized when
|a|^2+|b|^2=1 ([0.6,0.8]); Grover needs ~(pi/4)sqrt(N) iterations (N=4 -> 1). Wrong claim caught; NA."""
from __future__ import annotations
from concordance.verifiers import quantum_computing as QC


def test_qubit_normalization():
    assert QC.verify_qubit_normalization({"amplitudes": [0.6, 0.8], "claimed_normalized": True}).status == "CONFIRMED"
    assert QC.verify_qubit_normalization({"amplitudes": [0.6, 0.6], "claimed_normalized": True}).status == "MISMATCH"
    assert QC.verify_qubit_normalization({}).status == "NOT_APPLICABLE"


def test_grover_iterations():
    assert QC.verify_grover_iterations({"n_items": 4, "claimed_grover_iterations": 1}).status == "CONFIRMED"
    assert QC.verify_grover_iterations({"n_items": 4, "claimed_grover_iterations": 5}).status == "MISMATCH"


def test_born_rule():
    # 2026-10-13: P_i = |a_i|^2 / Σ|a_j|^2 — probability is amplitude squared (the double-slit's law).
    assert QC.verify_born_rule({"amplitudes": [0.6, 0.8], "outcome_index": 1,
                                "claimed_probability": 0.64}).status == "CONFIRMED"   # 0.8^2
    assert QC.verify_born_rule({"amplitudes": [1, 1], "outcome_index": 0,
                                "claimed_probability": 0.5}).status == "CONFIRMED"     # unnormalized → /Σ
    assert QC.verify_born_rule({"amplitudes": [0.6, 0.8], "outcome_index": 0,
                                "claimed_probability": 0.64}).status == "MISMATCH"     # P(0)=0.36
    assert QC.verify_born_rule({"amplitudes": [0.6, 0.8], "outcome_index": 5,
                                "claimed_probability": 0.1}).status == "ERROR"         # index out of range
    assert QC.verify_born_rule({"amplitudes": [0.6, 0.8]}).status == "NOT_APPLICABLE"
