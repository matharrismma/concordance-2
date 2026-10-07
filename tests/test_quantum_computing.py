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
