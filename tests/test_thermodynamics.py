"""Unit-pin the thermodynamics verifier (A2: verifier test-depth, 2026-10-06).
The molar gas constant R = 8.314 J/mol/K (verified through the engine's attested constant). Wrong claim
caught; missing field NOT_APPLICABLE.
"""
from __future__ import annotations

from concordance.verifiers import thermodynamics as T


def test_gas_constant():
    assert T.verify_gas_constant({"claimed_gas_constant_j_per_mol_k": 8.314}).status == "CONFIRMED"
    assert T.verify_gas_constant({"claimed_gas_constant_j_per_mol_k": 8.0}).status == "MISMATCH"


def test_missing_fields_never_false_pass():
    assert T.verify_entropy_change({}).status == "NOT_APPLICABLE"
    assert T.verify_carnot_efficiency({}).status == "NOT_APPLICABLE"
