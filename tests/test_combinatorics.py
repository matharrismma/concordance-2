"""Unit-pin the combinatorics verifier (A2, 2026-10-06). C(5,2)=10; P(5,2)=20."""
from __future__ import annotations
from concordance.verifiers import combinatorics as C


def test_combinations():
    assert C.verify_combinations({"comb_n": 5, "comb_k": 2, "claimed_combinations": 10}).status == "CONFIRMED"
    assert C.verify_combinations({"comb_n": 5, "comb_k": 2, "claimed_combinations": 8}).status == "MISMATCH"
    assert C.verify_combinations({}).status == "NOT_APPLICABLE"


def test_permutations():
    assert C.verify_permutations({"perm_n": 5, "perm_k": 2, "claimed_permutations": 20}).status == "CONFIRMED"
    assert C.verify_permutations({"perm_n": 5, "perm_k": 2, "claimed_permutations": 10}).status == "MISMATCH"
