"""Unit-pin the electrochemistry verifier (A2, 2026-10-06). The Faraday constant is 96485 C/mol."""
from __future__ import annotations
from concordance.verifiers import electrochemistry as EC


def test_faraday_constant():
    assert EC.verify_faraday_constant({"claimed_faraday_c_per_mol": 96485}).status == "CONFIRMED"
    assert EC.verify_faraday_constant({"claimed_faraday_c_per_mol": 90000}).status == "MISMATCH"


def test_missing_fields_never_false_pass():
    assert EC.verify_nernst({}).status == "NOT_APPLICABLE"
    assert EC.verify_faraday({}).status == "NOT_APPLICABLE"
