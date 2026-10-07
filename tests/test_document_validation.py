"""Unit-pin the document_validation verifier (A2, 2026-10-06). 79927398713 is a classic valid Luhn
number; flipping a digit breaks the checksum. Missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import document_validation as DV


def test_luhn():
    assert DV.verify_luhn({"luhn_number": "79927398713", "claimed_luhn_valid": True}).status == "CONFIRMED"
    assert DV.verify_luhn({"luhn_number": "79927398713", "claimed_luhn_valid": False}).status == "MISMATCH"
    assert DV.verify_luhn({}).status == "NOT_APPLICABLE"
