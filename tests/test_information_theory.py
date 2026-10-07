"""Unit-pin the information_theory verifier (A2, 2026-10-06). Shannon entropy of a fair bit = 1 bit;
Hamming distance(1010, 1001) = 2."""
from __future__ import annotations
from concordance.verifiers import information_theory as IT


def test_shannon_entropy():
    assert IT.verify_shannon_entropy({"probabilities": [0.5, 0.5], "claimed_entropy_bits": 1.0}).status == "CONFIRMED"
    assert IT.verify_shannon_entropy({"probabilities": [0.5, 0.5], "claimed_entropy_bits": 2.0}).status == "MISMATCH"
    assert IT.verify_shannon_entropy({}).status == "NOT_APPLICABLE"


def test_hamming_distance():
    assert IT.verify_hamming_distance({"string_a": "1010", "string_b": "1001", "claimed_hamming": 2}).status == "CONFIRMED"
    assert IT.verify_hamming_distance({"string_a": "1010", "string_b": "1001", "claimed_hamming": 3}).status == "MISMATCH"
