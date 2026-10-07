"""Unit-pin the cryptography verifier (A2, 2026-10-06). SHA-256 is a strong hash; a wrong strength claim
is caught; a missing field is NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import cryptography as CR


def test_hash_strength():
    assert CR.verify_hash_strength({"hash_strength_algorithm": "sha256", "claimed_hash_strength": "strong"}).status == "CONFIRMED"
    assert CR.verify_hash_strength({"hash_strength_algorithm": "sha256", "claimed_hash_strength": "weak"}).status == "MISMATCH"
    assert CR.verify_hash_strength({}).status == "NOT_APPLICABLE"
