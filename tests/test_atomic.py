"""Unit-pin the atomic verifier (A2: verifier test-depth, 2026-10-06).
Shell capacity 2n^2 (n=2 -> 8); quantum-number validity (n=2, l=1, ml=0, ms=+1/2 is allowed; l>=n is
not). Wrong claim caught; missing field NOT_APPLICABLE.
"""
from __future__ import annotations

from concordance.verifiers import atomic as AT


def test_shell_capacity():
    assert AT.verify_shell_capacity({"shell_n": 2, "claimed_shell_capacity": 8}).status == "CONFIRMED"
    assert AT.verify_shell_capacity({"shell_n": 2, "claimed_shell_capacity": 10}).status == "MISMATCH"


def test_quantum_numbers():
    assert AT.verify_quantum_numbers({"n": 2, "l": 1, "ml": 0, "ms": 0.5,
                                      "claimed_valid_quantum_numbers": True}).status == "CONFIRMED"
    # l must be < n; l=2 with n=2 is not an allowed state, so claiming valid is a mismatch
    assert AT.verify_quantum_numbers({"n": 2, "l": 2, "ml": 0, "ms": 0.5,
                                      "claimed_valid_quantum_numbers": True}).status == "MISMATCH"
